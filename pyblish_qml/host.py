import os
import sys
import inspect
import traceback

import pyblish.api

from . import ipc, settings, _state
from .vendor.Qt import QtWidgets, QtCore, QtGui

MODULE_DIR = os.path.dirname(__file__)
SPLASH_PATH = os.path.join(MODULE_DIR, "splash.png")


def register_dispatch_wrapper(wrapper):
    """Register a dispatch wrapper for servers

    The wrapper must have this exact signature:
        (func, *args, **kwargs)

    """

    signature = inspect.getargspec(wrapper)
    if any([len(signature.args) != 1,
            signature.varargs is None,
            signature.keywords is None]):
        raise TypeError("Wrapper signature mismatch")

    _state["dispatchWrapper"] = wrapper


def deregister_dispatch_wrapper():
    _state.pop("dispatchWrapper")


def dispatch_wrapper():
    return _state.get("dispatchWrapper")


def current_server():
    return _state.get("currentServer")


def install(modal):
    """Perform first time install

    Attributes:
        initial_port (int, optional): Port from which to start
            looking for available ports, defaults to 9001

    """

    if _state.get("installed"):
        sys.stdout.write("Already installed, uninstalling..\n")
        uninstall()

    install_callbacks()
    install_host(modal)

    _state["installed"] = True


def uninstall():
    """Clean up traces of Pyblish QML"""
    uninstall_callbacks()
    sys.stdout.write("Pyblish QML shutdown successful.\n")


def show(parent=None, targets=[], modal=None):
    """Attempt to show GUI

    Requires install() to have been run first, and
    a live instance of Pyblish QML in the background.

    """

    # Get modal mode from environment
    if modal is None:
        modal = bool(os.environ.get("PYBLISH_QML_MODAL", False))

    # Automatically install if not already installed.
    if not _state.get("installed"):
        install(modal)

    # Show existing GUI
    if _state.get("currentServer"):
        server = _state["currentServer"]
        proxy = ipc.server.Proxy(server)

        try:
            proxy.show(settings.to_dict())
            return server

        except IOError:
            # The running instance has already been closed.
            _state.pop("currentServer")

    splash = Splash()
    splash.show()

    def on_shown():
        try:
            splash.close()

        except RuntimeError:
            # Splash already closed
            pass

        pyblish.api.deregister_callback(*callback)

    callback = "pyblishQmlShown", on_shown
    pyblish.api.register_callback(*callback)

    try:
        service = ipc.service.Service()
        server = ipc.server.Server(service, targets=targets, modal=modal)
    except Exception:
        # If for some reason, the GUI fails to show.
        traceback.print_exc()
        return on_shown()

    proxy = ipc.server.Proxy(server)
    proxy.show(settings.to_dict())

    # Store reference to server for future calls
    _state["currentServer"] = server

    print("Success. QML server available as "
          "pyblish_qml.api.current_server()")

    server.listen()

    return server


def publish():
    # get existing GUI
    if _state.get("currentServer"):
        server = _state["currentServer"]
        proxy = ipc.server.Proxy(server)

        try:
            proxy.publish()

        except IOError:
            # The running instance has already been closed.
            _state.pop("currentServer")


def validate():
    # get existing GUI
    if _state.get("currentServer"):
        server = _state["currentServer"]
        proxy = ipc.server.Proxy(server)

        try:
            proxy.validate()

        except IOError:
            # The running instance has already been closed.
            _state.pop("currentServer")


def install_callbacks():
    pyblish.api.register_callback("instanceToggled", _toggle_instance)
    pyblish.api.register_callback("pluginToggled", _toggle_plugin)


def uninstall_callbacks():
    pyblish.api.deregister_callback("instanceToggled", _toggle_instance)
    pyblish.api.deregister_callback("pluginToggled", _toggle_plugin)


def _toggle_instance(instance, new_value, old_value):
    """Alter instance upon visually toggling it"""
    instance.data["publish"] = new_value


def _toggle_plugin(plugin, new_value, old_value):
    """Alter plugin upon visually toggling it"""
    plugin.active = new_value


def register_python_executable(path):
    """Expose Python executable to server

    The Python executable must be compatible with the
    version of PyQt5 installed or provided on the system.

    """

    assert os.path.isfile(path), "Must be a file, such as python.exe"

    _state["pythonExecutable"] = path


def registered_python_executable():
    return _state.get("pythonExecutable")


def register_pyqt5(path):
    """Expose PyQt5 to Python

    The exposed PyQt5 must be compatible with the exposed Python.

    Arguments:
        path (str): Absolute path to directory containing PyQt5

    """

    _state["pyqt5"] = path


def install_host(modal):
    """Install required components into supported hosts

    An unsupported host will still run, but may encounter issues,
    especially with threading.

    """

    for install in (_install_maya,
                    _install_houdini,
                    _install_nuke,
                    _install_hiero,
                    _install_nukestudio):
        try:
            install(modal)
        except ImportError:
            pass
        else:
            break


def _on_application_quit():
    """Automatically kill QML on host exit"""

    try:
        _state["currentServer"].popen.kill()

    except KeyError:
        # No server started
        pass

    except OSError:
        # Already dead
        pass


def _connect_host_event(app):
    """Connect some event from host to QML

    Host will connect following event to QML:
    QEvent.Show                -> rise QML
    QEvent.Hide                -> hide QML
    QEvent.WindowActivate      -> set QML on top
    QEvent.WindowDeactivate    -> remove QML on top
    """

    class HostEventFilter(QtWidgets.QWidget):

        eventList = [
            QtCore.QEvent.Show,
            QtCore.QEvent.Hide,
            QtCore.QEvent.WindowActivate,
            QtCore.QEvent.WindowDeactivate
        ]

        def getServer(self):
            server = None
            try:
                server = _state["currentServer"]
            except KeyError:
                # No server started
                pass
            return server

        def eventFilter(self, widget, event):
            if event.type() in self.eventList:
                server = self.getServer()
                if not server:
                    return False
                else:
                    proxy = ipc.server.Proxy(server)

                if event.type() == QtCore.QEvent.Show:
                    try:
                        proxy.rise()
                        return True
                    except IOError:
                        # The running instance has already been closed.
                        _state.pop("currentServer")
                if event.type() == QtCore.QEvent.Hide:
                    try:
                        proxy.hide()
                        return True
                    except IOError:
                        # The running instance has already been closed.
                        _state.pop("currentServer")
                if event.type() == QtCore.QEvent.WindowActivate:
                    try:
                        proxy.inFocus()
                        return True
                    except IOError:
                        # The running instance has already been closed.
                        _state.pop("currentServer")
                if event.type() == QtCore.QEvent.WindowDeactivate:
                    try:
                        proxy.outFocus()
                        return True
                    except IOError:
                        # The running instance has already been closed.
                        _state.pop("currentServer")
            return False

    # Get top window in host
    app_top_window = app.activeWindow()
    while True:
        parent_window = app_top_window.parent()
        if parent_window:
            app_top_window = parent_window
        else:
            break
    # install event filter
    try:
        host_event_filter = HostEventFilter(app_top_window)
        app_top_window.installEventFilter(host_event_filter)
    except Exception:
        pass


def _install_maya(modal):
    """Helper function to Autodesk Maya support"""
    from maya import utils

    def threaded_wrapper(func, *args, **kwargs):
        return utils.executeInMainThreadWithResult(
            func, *args, **kwargs)

    sys.stdout.write("Setting up Pyblish QML in Maya\n")
    if not modal:
        register_dispatch_wrapper(threaded_wrapper)

    app = QtWidgets.QApplication.instance()
    app.aboutToQuit.connect(_on_application_quit)
    _connect_host_event(app)

    if settings.ContextLabel == settings.ContextLabelDefault:
        settings.ContextLabel = "Maya"
    if settings.WindowTitle == settings.WindowTitleDefault:
        settings.WindowTitle = "Pyblish (Maya)"


def _install_houdini(modal):
    """Helper function to SideFx Houdini support"""
    import hdefereval

    def threaded_wrapper(func, *args, **kwargs):
        return hdefereval.executeInMainThreadWithResult(
            func, *args, **kwargs)

    sys.stdout.write("Setting up Pyblish QML in Houdini\n")
    if not modal:
        register_dispatch_wrapper(threaded_wrapper)

    app = QtWidgets.QApplication.instance()
    app.aboutToQuit.connect(_on_application_quit)
    _connect_host_event(app)

    if settings.ContextLabel == settings.ContextLabelDefault:
        settings.ContextLabel = "Houdini"
    if settings.WindowTitle == settings.WindowTitleDefault:
        settings.WindowTitle = "Pyblish (Houdini)"


def _install_nuke(modal):
    """Helper function to The Foundry Nuke support"""
    import nuke

    if "--hiero" in nuke.rawArgs or "--studio" in nuke.rawArgs:
        raise ImportError

    def threaded_wrapper(func, *args, **kwargs):
        return nuke.executeInMainThreadWithResult(
            func, args, kwargs)

    sys.stdout.write("Setting up Pyblish QML in Nuke\n")
    if not modal:
        register_dispatch_wrapper(threaded_wrapper)

    app = QtWidgets.QApplication.instance()
    app.aboutToQuit.connect(_on_application_quit)
    _connect_host_event(app)

    if settings.ContextLabel == settings.ContextLabelDefault:
        settings.ContextLabel = "Nuke"
    if settings.WindowTitle == settings.WindowTitleDefault:
        settings.WindowTitle = "Pyblish (Nuke)"


def _install_hiero(modal):
    """Helper function to The Foundry Hiero support"""
    import hiero
    import nuke

    if "--hiero" not in nuke.rawArgs:
        raise ImportError

    def threaded_wrapper(func, *args, **kwargs):
        return hiero.core.executeInMainThreadWithResult(
            func, args, kwargs)

    sys.stdout.write("Setting up Pyblish QML in Hiero\n")
    if not modal:
        register_dispatch_wrapper(threaded_wrapper)

    app = QtWidgets.QApplication.instance()
    app.aboutToQuit.connect(_on_application_quit)
    _connect_host_event(app)

    if settings.ContextLabel == settings.ContextLabelDefault:
        settings.ContextLabel = "Hiero"
    if settings.WindowTitle == settings.WindowTitleDefault:
        settings.WindowTitle = "Pyblish (Hiero)"


def _install_nukestudio(modal):
    """Helper function to The Foundry Hiero support"""
    import nuke

    if "--studio" not in nuke.rawArgs:
        raise ImportError

    def threaded_wrapper(func, *args, **kwargs):
        return nuke.executeInMainThreadWithResult(
            func, args, kwargs)

    sys.stdout.write("Setting up Pyblish QML in NukeStudio\n")
    if not modal:
        register_dispatch_wrapper(threaded_wrapper)

    app = QtWidgets.QApplication.instance()
    app.aboutToQuit.connect(_on_application_quit)
    _connect_host_event(app)

    if settings.ContextLabel == settings.ContextLabelDefault:
        settings.ContextLabel = "NukeStudio"
    if settings.WindowTitle == settings.WindowTitleDefault:
        settings.WindowTitle = "Pyblish (NukeStudio)"


class Splash(QtWidgets.QWidget):
    """Splash screen for loading QML via subprocess

    Loading pyblish-qml may take some time, so when loading
    from within an existing interpreter, such as Maya, this
    splash screen can keep the user company during that time.

    """

    def __init__(self, parent=None):
        super(Splash, self).__init__(parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.FramelessWindowHint
        )

        pixmap = QtGui.QPixmap(SPLASH_PATH)
        image = QtWidgets.QLabel()
        image.setPixmap(pixmap)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(image)

        label = QtWidgets.QLabel(self)
        label.move(20, 170)
        label.show()

        self.count = 0
        self.label = label

        self.setStyleSheet("""
            QLabel {
                color: white
            }
        """)

        loop = QtCore.QTimer()
        loop.timeout.connect(self.animate)
        loop.start(330)

        self.loop = loop

        self.animate()
        self.resize(200, 200)

    def animate(self):
        self.label.setText("loading" + "." * self.count)
        self.count = (self.count + 1) % 4
