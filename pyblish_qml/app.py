"""Application entry-point"""

# Standard library
import os
import sys
import time
import threading

# Dependencies
from PyQt5 import QtCore, QtGui, QtQuick, QtTest

# Local libraries
from . import util, compat, server, control, rpc, settings

MODULE_DIR = os.path.dirname(__file__)
QML_IMPORT_DIR = os.path.join(MODULE_DIR, "qml")
APP_PATH = os.path.join(MODULE_DIR, "qml", "main.qml")
ICON_PATH = os.path.join(MODULE_DIR, "icon.ico")


class Window(QtQuick.QQuickView):
    """Main application window"""

    def __init__(self, parent=None):
        super(Window, self).__init__(None)
        self.parent = parent

        self.setTitle(settings.WindowTitle)
        self.setResizeMode(self.SizeRootObjectToView)

        self.resize(*settings.WindowSize)
        self.setMinimumSize(QtCore.QSize(430, 300))

    def event(self, event):
        """Allow GUI to be closed upon holding Shift"""
        if event.type() == QtCore.QEvent.Close:
            modifiers = self.parent.queryKeyboardModifiers()
            shift_pressed = QtCore.Qt.ShiftModifier & modifiers

            if shift_pressed or hasattr(self.parent, "__debugging__"):
                event.accept()

            elif "publishing" in self.parent.controller.states:
                event.ignore()

            else:
                event.ignore()
                self.parent.hide()

        return super(Window, self).event(event)


class Application(QtGui.QGuiApplication):
    """Pyblish QML wrapper around QGuiApplication

    Provides production and debug launchers along with controller
    initialisation and orchestration.

    """

    show_signal = QtCore.pyqtSignal(int, QtCore.QVariant)
    hide_signal = QtCore.pyqtSignal()
    quit_signal = QtCore.pyqtSignal()
    app_message = QtCore.pyqtSignal(str)
    standalone_signal = QtCore.pyqtSignal()

    def __init__(self, source):
        super(Application, self).__init__(sys.argv)

        self.setWindowIcon(QtGui.QIcon(ICON_PATH))

        window = Window(self)
        window.statusChanged.connect(self.on_status_changed)

        engine = window.engine()
        engine.addImportPath(QML_IMPORT_DIR)

        controller = control.Controller()

        context = engine.rootContext()
        context.setContextProperty("app", controller)

        self.window = window
        self.engine = engine
        self.controller = controller
        self.clients = dict()
        self.current_client = None

        self.show_signal.connect(self.show)
        self.hide_signal.connect(self.hide)
        self.quit_signal.connect(self.quit)
        self.standalone_signal.connect(self.on_standalone)

        window.setSource(QtCore.QUrl.fromLocalFile(source))

    def on_status_changed(self, status):
        if status == QtQuick.QQuickView.Error:
            self.quit()

    def register_heartbeat(self, port):
        if port not in self.clients:
            self.register_client(port)
        self.clients[port]["lastSeen"] = time.time()

    def register_client(self, port):
        self.current_client = port
        self.clients[port] = {
            "lastSeen": time.time()
        }

    def deregister_client(self, port):
        self.clients.pop(port)

    def show(self, port, client_settings=None):
        """Display GUI

        Once the QML interface has been loaded, use this
        to display it.

        Arguments:
            port (int): Client asking to show GUI.
            client_settings (dict, optional): Visual settings, see settings.py

        """

        window = self.window

        if client_settings:
            # Apply client-side settings
            settings.from_dict(client_settings)
            window.setWidth(client_settings["WindowSize"][0])
            window.setHeight(client_settings["WindowSize"][1])
            window.setTitle(client_settings["WindowTitle"])

        print("Settings:")
        for key, value in client_settings.items():
            print("  %s = %s" % (key, value))

        previously_hidden = not window.isVisible()

        window.requestActivate()
        window.showNormal()

        new_client = False
        if settings.current_host_port() != port:
            new_client = True
            settings.set_current_host_port(port)

        if os.name == "nt":
            # Work-around for window appearing behind
            # other windows upon being shown once hidden.
            previous_flags = window.flags()
            window.setFlags(previous_flags | QtCore.Qt.WindowStaysOnTopHint)
            window.setFlags(previous_flags)

        if previously_hidden or new_client:
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
            self.controller.reset()

    def hide(self):
        """Hide GUI

        Process remains active and may be shown
        via a call to `show()`

        """

        self.window.hide()

    def on_standalone(self):
        """The process is running solo"""
        self.app_message.emit("Running standalone")
        if not hasattr(self, "__debugging__"):
            print("Quitting due to loneliness")
            time.sleep(1)
            self.quit()

    def listen(self):
        """Listen on incoming messages from host

        Usage:
            >> from pyblish_qml import client
            >> proxy = client.proxy()
            >> proxy.show()   # Show a hidden GUI
            >> proxy.close()  # Close GUI permanently
            >> proxy.kill()   # Close GUI forcefully (careful)

        """

        kwargs = {
            "port": 9090,
            "service": server.QmlApi(self),
        }

        t = threading.Thread(target=server._serve, kwargs=kwargs)
        t.daemon = True
        t.start()


def main(source=None, debug=False, validate=True):
    """Start the Qt-runtime and show the window

    Arguments:
        source (str): QML entry-point
        debug (bool, optional): Run in debug-mode. Defaults to False
        validate (bool, optional): Whether the environment should be validated
            prior to launching. Defaults to True

    """

    # Initialise OS compatiblity
    compat.main()

    print("Starting Pyblish..")
    util.timer("application")

    # debug mode
    if debug:
        port = 6000

        app = Application(source or APP_PATH)
        app.listen()
        app.__debugging__ = True

        print("Starting in debug-mode")
        print("Looking for server..")
        proxy = rpc.client.Proxy(port)

        if not proxy.ping():
            os.environ["PYBLISH_CLIENT_PORT"] = str(port)

            print("No existing server found, creating..")
            thread = threading.Thread(
                target=rpc.server.start_debug_server,
                kwargs={"port": port})
            thread.daemon = True
            thread.start()

            print("Debug server created successfully.")
            print("Running mocked RPC server @ 127.0.0.1:%s" % port)

        app.show_signal.emit(port, {
            "ContextLabel": "World",
            "WindowTitle": "Pyblish (DEBUG)",
            "WindowSize": (430, 600)
        })

    else:
        app = Application(source or APP_PATH)
        app.listen()

    util.timer_end("application", "Spent %.2f ms creating the application")

    return app.exec_()


if __name__ == "__main__":
    main(debug=True,
         validate=False)
