"""Application entry-point"""

# Standard library
import os
import sys
import time
import json
import traceback
import threading

# Dependencies
from PyQt5 import QtCore, QtGui, QtQuick, QtTest

# Local libraries
from . import util, compat, control, settings, ipc

MODULE_DIR = os.path.dirname(__file__)
QML_IMPORT_DIR = os.path.join(MODULE_DIR, "qml")
APP_PATH = os.path.join(MODULE_DIR, "qml", "main.qml")
ICON_PATH = os.path.join(MODULE_DIR, "icon.ico")


class Window(QtQuick.QQuickView):
    """Main application window"""

    def __init__(self):
        super(Window, self).__init__(None)
        self.app = QtGui.QGuiApplication.instance()

        self.setTitle(settings.WindowTitle)
        self.setResizeMode(self.SizeRootObjectToView)

        self.resize(*settings.WindowSize)
        self.setMinimumSize(QtCore.QSize(430, 300))

    def event(self, event):
        """Allow GUI to be closed upon holding Shift"""
        if event.type() == QtCore.QEvent.Close:
            modifiers = self.app.queryKeyboardModifiers()
            shift_pressed = QtCore.Qt.ShiftModifier & modifiers
            states = self.app.controller.states

            if shift_pressed:
                print("Force quitted..")
                self.app.controller.host.emit("pyblishQmlCloseForced")
                event.accept()

            elif any(state in states for state in ("ready", "finished")):
                self.app.controller.host.emit("pyblishQmlClose")
                event.accept()

            else:
                print("Not ready, hold SHIFT to force an exit")
                event.ignore()

        return super(Window, self).event(event)


class NativeVessel(QtGui.QWindow):
    """Container window"""

    def __init__(self):
        super(NativeVessel, self).__init__(None)
        self.app = QtGui.QGuiApplication.instance()

    def resizeEvent(self, event):
        self.app.resize(self.width(), self.height())

    def event(self, event):
        # Is required when Foster mode is on.
        # Native vessel will receive closeEvent while foster mode is on
        # and is the parent of window.
        if event.type() == QtCore.QEvent.Close:
            self.app.window.event(event)
            if event.isAccepted():
                # `app.fostered` is False at this moment.
                self.app.quit()

        return super(NativeVessel, self).event(event)


class Application(QtGui.QGuiApplication):
    """Pyblish QML wrapper around QGuiApplication

    Provides production and debug launchers along with controller
    initialisation and orchestration.

    """

    shown = QtCore.pyqtSignal(*(QtCore.QVariant,) * 3)
    hidden = QtCore.pyqtSignal()
    quitted = QtCore.pyqtSignal()
    published = QtCore.pyqtSignal()
    validated = QtCore.pyqtSignal()

    resized = QtCore.pyqtSignal(QtCore.QVariant, QtCore.QVariant)

    risen = QtCore.pyqtSignal()
    inFocused = QtCore.pyqtSignal()
    outFocused = QtCore.pyqtSignal()

    attached = QtCore.pyqtSignal(QtCore.QVariant)
    detached = QtCore.pyqtSignal()
    host_attached = QtCore.pyqtSignal()
    host_detached = QtCore.pyqtSignal()

    def __init__(self, source, targets=[]):
        super(Application, self).__init__(sys.argv)

        self.setWindowIcon(QtGui.QIcon(ICON_PATH))

        native_vessel = NativeVessel()

        window = Window()
        window.statusChanged.connect(self.on_status_changed)

        engine = window.engine()
        engine.addImportPath(QML_IMPORT_DIR)

        host = ipc.client.Proxy()
        controller = control.Controller(host, targets=targets)
        controller.finished.connect(lambda: window.alert(0))

        context = engine.rootContext()
        context.setContextProperty("app", controller)

        self.fostered = False
        self.foster_fixed = False

        self.foster_vessel = None
        self.native_vessel = native_vessel

        self.window = window
        self.engine = engine
        self.controller = controller
        self.host = host
        self.clients = dict()
        self.current_client = None

        self.shown.connect(self.show)
        self.hidden.connect(self.hide)
        self.quitted.connect(self.quit)
        self.published.connect(self.publish)
        self.validated.connect(self.validate)

        self.resized.connect(self.resize)

        self.risen.connect(self.rise)
        self.inFocused.connect(self.inFocus)
        self.outFocused.connect(self.outFocus)

        self.attached.connect(self.attach)
        self.detached.connect(self.detach)

        window.setSource(QtCore.QUrl.fromLocalFile(source))

    def on_status_changed(self, status):
        if status == QtQuick.QQuickView.Error:
            self.quit()

    def register_client(self, port):
        self.current_client = port
        self.clients[port] = {
            "lastSeen": time.time()
        }

    def deregister_client(self, port):
        self.clients.pop(port)

    def quit(self):
        event = None
        if self.fostered:
            # Foster vessel's closeEvent will trigger "quit" which connected
            # to here.
            # Forward the event to window.
            event = QtCore.QEvent(QtCore.QEvent.Close)
            self.window.event(event)

        if event is None or event.isAccepted():
            super(Application, self).quit()

    @util.SlotSentinel()
    def show(self, client_settings=None, window_id=None, foster_fixed=False):
        """Display GUI

        Once the QML interface has been loaded, use this
        to display it.

        Arguments:
            port (int): Client asking to show GUI.
            client_settings (dict, optional): Visual settings, see settings.py

        """
        self.fostered = window_id is not None

        if self.fostered:
            print("Moving to container window ...")

            # Creates a local representation of a window created by another
            # process (Maya or other host).
            foster_vessel = QtGui.QWindow.fromWinId(window_id)

            if foster_vessel is None:
                raise RuntimeError("Container window not found, ID: {}\n."
                                   "This is a bug.".format(window_id))

            self.window.setParent(foster_vessel)
            self.foster_vessel = foster_vessel
            self.foster_fixed = foster_fixed

        if client_settings:
            # Apply client-side settings
            settings.from_dict(client_settings)

            def first_appearance_setup(vessel):
                vessel.setGeometry(client_settings["WindowPosition"][0],
                                   client_settings["WindowPosition"][1],
                                   client_settings["WindowSize"][0],
                                   client_settings["WindowSize"][1])
                vessel.setTitle(client_settings["WindowTitle"])

            first_appearance_setup(self.native_vessel)

            if self.fostered:
                if not self.foster_fixed:
                    # Return it back to native vessel for first run
                    self.window.setParent(self.native_vessel)
                first_appearance_setup(self.foster_vessel)

        message = list()
        message.append("Settings: ")
        for key, value in settings.to_dict().items():
            message.append("  %s = %s" % (key, value))

        print("\n".join(message))

        if self.fostered and not self.foster_fixed:
            self.native_vessel.show()

        self.window.requestActivate()
        self.window.showNormal()

        self._popup()

        # Give statemachine enough time to boot up
        if not any(state in self.controller.states
                   for state in ["ready", "finished"]):
            util.timer("ready")

            ready = QtTest.QSignalSpy(self.controller.ready)

            count = len(ready)
            ready.wait(1000)
            if len(ready) != count + 1:
                print("Warning: Could not enter ready state")

            util.timer_end("ready", "Awaited statemachine for %.2f ms")

        self.controller.show.emit()

        # Allow time for QML to initialise
        util.schedule(self.controller.reset, 500, channel="main")

    def hide(self):
        """Hide GUI

        Process remains active and may be shown
        via a call to `show()`

        """
        self.window.hide()

    def rise(self):
        """Rise GUI from hidden"""
        self.window.show()

    def inFocus(self):
        """Set GUI on-top flag"""
        if not self.fostered:
            previous_flags = self.window.flags()
            self.window.setFlags(previous_flags |
                                 QtCore.Qt.WindowStaysOnTopHint)

    def outFocus(self):
        """Remove GUI on-top flag"""
        if not self.fostered:
            previous_flags = self.window.flags()
            self.window.setFlags(previous_flags ^
                                 QtCore.Qt.WindowStaysOnTopHint)

    def resize(self, width, height):
        """Resize GUI with it's vessel (container window)
        """
        # (NOTE) Could not get it auto resize with container, this is a
        #   alternative
        self.window.resize(width, height)

    def _popup(self):
        if not self.fostered:
            window = self.window
            # Work-around for window appearing behind
            # other windows upon being shown once hidden.
            previous_flags = window.flags()
            window.setFlags(previous_flags | QtCore.Qt.WindowStaysOnTopHint)
            window.setFlags(previous_flags)

    def detach(self):
        """Detach QQuickView window from the host

        In foster mode, inorder to prevent window freeze when the host's
        main thread is busy, will detach the QML window from the container
        inside the host, and re-parent to the container which spawned by
        the subprocess. And attach it back to host when the heavy lifting
        is done.

        This is the part that detaching from host.

        """
        if self.foster_fixed or self.foster_vessel is None:
            self.controller.detached.emit()
            return

        print("Detach window from foster parent...")

        self.fostered = False
        self.window.setParent(self.native_vessel)

        # Show dst container
        self.native_vessel.show()
        self.native_vessel.setGeometry(self.foster_vessel.geometry())
        self.native_vessel.setOpacity(1)
        # Hide src container (will wait for host)
        host_detached = QtTest.QSignalSpy(self.host_detached)
        self.host.detach()
        host_detached.wait(300)
        # Stay on top
        self.window.requestActivate()
        self._popup()

        self.controller.detached.emit()

    def attach(self, alert=False):
        """Attach QQuickView window to the host

        In foster mode, inorder to prevent window freeze when the host's
        main thread is busy, will detach the QML window from the container
        inside the host, and re-parent to the container which spawned by
        the subprocess. And attach it back to host when the heavy lifting
        is done.

        This is the part that attaching back to host.

        """
        if self.foster_fixed or self.foster_vessel is None:
            self.controller.attached.emit()
            if self.foster_vessel is not None:
                self.host.popup(alert)  # Send alert
            return

        print("Attach window to foster parent...")

        self.fostered = True
        self.window.setParent(self.foster_vessel)

        # Show dst container (will wait for host)
        host_attached = QtTest.QSignalSpy(self.host_attached)
        self.host.attach(self.native_vessel.geometry())
        host_attached.wait(300)
        # Hide src container
        self.native_vessel.setOpacity(0)  # avoid hide window anim
        self.native_vessel.hide()
        # Stay on top
        self.host.popup(alert)

        self.controller.attached.emit()

    def publish(self):
        """Fire up the publish sequence"""
        self.controller.publish()

    def validate(self):
        """Fire up the validation sequance"""
        self.controller.validate()

    def listen(self):
        """Listen on incoming messages from host

        TODO(marcus): We can't use this, as we are already listening on stdin
            through client.py. Do use this, we will have to find a way to
            receive multiple signals from the same stdin, and channel them
            to their corresponding source.

        """

        def _listen():
            while True:
                line = self.host.channels["parent"].get()
                payload = json.loads(line)["payload"]

                # We can't call methods directly, as we are running
                # in a thread. Instead, we emit signals that do the
                # job for us.
                signal = {

                    "show": "shown",
                    "hide": "hidden",
                    "quit": "quitted",
                    "publish": "published",
                    "validate": "validated",

                    "resize": "resized",

                    "rise": "risen",
                    "inFocus": "inFocused",
                    "outFocus": "outFocused",

                    "attach": "attached",
                    "detach": "detached",
                    "host_attach": "host_attached",
                    "host_detach": "host_detached",

                }.get(payload["name"])

                if not signal:
                    print("'{name}' was unavailable.".format(
                        **payload))
                else:
                    try:
                        getattr(self, signal).emit(
                            *payload.get("args", []))
                    except Exception:
                        traceback.print_exc()

        thread = threading.Thread(target=_listen)
        thread.daemon = True
        thread.start()


def main(demo=False, aschild=False, targets=[]):
    """Start the Qt-runtime and show the window

    Arguments:
        aschild (bool, optional): Run as child of parent process

    """

    if aschild:
        print("Starting pyblish-qml")
        compat.main()
        app = Application(APP_PATH, targets)
        app.listen()

        print("Done, don't forget to call `show()`")
        return app.exec_()

    else:
        print("Starting pyblish-qml server..")
        service = ipc.service.MockService() if demo else ipc.service.Service()
        server = ipc.server.Server(service, targets=targets)

        proxy = ipc.server.Proxy(server)
        proxy.show(settings.to_dict())

        server.listen()
        server.wait()
