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

        self.setTitle(settings.WindowTitle)
        self.setResizeMode(self.SizeRootObjectToView)

        self.resize(*settings.WindowSize)
        self.setMinimumSize(QtCore.QSize(430, 300))


class NativeVessel(QtGui.QWindow):
    """Container window"""

    def __init__(self, app):
        super(NativeVessel, self).__init__(None)
        self.app = app

    def resizeEvent(self, event):
        self.app.resize(self.width(), self.height())

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

        return super(NativeVessel, self).event(event)


class Application(QtGui.QGuiApplication):
    """Pyblish QML wrapper around QGuiApplication

    Provides production and debug launchers along with controller
    initialisation and orchestration.

    """

    shown = QtCore.pyqtSignal(QtCore.QVariant, QtCore.QVariant)
    hidden = QtCore.pyqtSignal()
    quitted = QtCore.pyqtSignal()
    published = QtCore.pyqtSignal()
    validated = QtCore.pyqtSignal()

    resized = QtCore.pyqtSignal(QtCore.QVariant, QtCore.QVariant)

    risen = QtCore.pyqtSignal()
    inFocused = QtCore.pyqtSignal()
    outFocused = QtCore.pyqtSignal()

    attached = QtCore.pyqtSignal()
    detached = QtCore.pyqtSignal()

    def __init__(self, source, targets=[]):
        super(Application, self).__init__(sys.argv)

        self.setWindowIcon(QtGui.QIcon(ICON_PATH))

        native_vessel = NativeVessel(self)

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

        self.foster_vessel = None
        self.vessel = self.native_vessel = native_vessel

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

    @util.SlotSentinel()
    def show(self, client_settings=None, window_id=None):
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

            self.vessel = self.foster_vessel = foster_vessel

        if client_settings:
            # Apply client-side settings
            settings.from_dict(client_settings)

            self.vessel.setWidth(client_settings["WindowSize"][0])
            self.vessel.setHeight(client_settings["WindowSize"][1])
            self.vessel.setTitle(client_settings["WindowTitle"])
            self.vessel.setFramePosition(
                QtCore.QPoint(
                    client_settings["WindowPosition"][0],
                    client_settings["WindowPosition"][1]
                )
            )

        message = list()
        message.append("Settings: ")
        for key, value in settings.to_dict().items():
            message.append("  %s = %s" % (key, value))

        print("\n".join(message))

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
        self.vessel.hide()

    def rise(self):
        """Rise GUI from hidden"""
        self.vessel.show()

    def inFocus(self):
        """Set GUI on-top flag"""
        if not self.fostered and os.name == "nt":
            previous_flags = self.window.flags()
            self.window.setFlags(previous_flags |
                                 QtCore.Qt.WindowStaysOnTopHint)

    def outFocus(self):
        """Remove GUI on-top flag"""
        if not self.fostered and os.name == "nt":
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
        if not self.fostered and os.name == "nt":
            window = self.window
            # Work-around for window appearing behind
            # other windows upon being shown once hidden.
            previous_flags = window.flags()
            window.setFlags(previous_flags | QtCore.Qt.WindowStaysOnTopHint)
            window.setFlags(previous_flags)

    def _set_goemetry(self, source, target):
        """Set window position and size after parent swap"""
        target.setFramePosition(source.framePosition())

        window_state = source.windowState()
        target.setWindowState(window_state)

        if not window_state == QtCore.Qt.WindowMaximized:
            target.resize(source.size())

    def detach(self):
        """Detach QQuickView window from the host

        In foster mode, inorder to prevent window freeze when the host's
        main thread is busy, will detach the QML window from the container
        inside the host, and re-parent to the container which spawned by
        the subprocess. And attach it back to host when the heavy lifting
        is done.

        This is the part that detaching from host.

        """
        if self.foster_vessel is None:
            self.controller.detached.emit()
            return

        print("Detach window from foster parent...")

        self.vessel = self.native_vessel

        self.host.detach()

        self.fostered = False
        self.vessel.show()

        self.window.setParent(self.vessel)
        self._set_goemetry(self.foster_vessel, self.vessel)
        self._popup()

        self.controller.detached.emit()

    def attach(self):
        """Attach QQuickView window to the host

        In foster mode, inorder to prevent window freeze when the host's
        main thread is busy, will detach the QML window from the container
        inside the host, and re-parent to the container which spawned by
        the subprocess. And attach it back to host when the heavy lifting
        is done.

        This is the part that attaching back to host.

        """
        if self.foster_vessel is None:
            self.controller.attached.emit()
            return

        print("Attach window to foster parent...")

        self.vessel = self.foster_vessel

        self.host.attach()

        self.native_vessel.hide()
        self.fostered = True

        self.window.setParent(self.vessel)
        self._set_goemetry(self.native_vessel, self.vessel)

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
