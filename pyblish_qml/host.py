import os
import sys
import inspect

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


def install():
    """Perform first time install

    Attributes:
        initial_port (int, optional): Port from which to start
            looking for available ports, defaults to 9001

    """

    if _state.get("installed"):
        sys.stdout.write("Already installed, uninstalling..\n")
        uninstall()

    install_callbacks()
    install_host()

    _state["installed"] = True


def uninstall():
    """Clean up traces of Pyblish QML"""
    uninstall_callbacks()
    sys.stdout.write("Pyblish QML shutdown successful.\n")


def show(parent=None):
    """Attempt to show GUI

    Requires install() to have been run first, and
    a live instance of Pyblish QML in the background.

    """

    # Automatically install if not already installed.
    if not _state.get("installed"):
        install()

    # Only allow a single instance at any time.
    if _state.get("currentServer"):
        _state.get("currentServer").stop()

    splash = Splash()
    splash.show()

    def on_shown():
        splash.close()
        pyblish.api.deregister_callback(*callback)

    callback = "pyblishQmlShown", on_shown
    pyblish.api.register_callback(*callback)

    server = ipc.server.Server(
        service=ipc.service.Service(),
    )

    _state["currentServer"] = server

    print("Available as pyblish_qml.api.current_server()")

    return server


def install_callbacks():
    pyblish.api.register_callback("instanceToggled", _toggle_instance)


def uninstall_callbacks():
    pyblish.api.deregister_callback("instanceToggled", _toggle_instance)


def _toggle_instance(instance, new_value, old_value):
    """Alter instance upon visually toggling instance"""
    instance.data["publish"] = new_value


def register_python_executable(path):
    _state["pythonExecutable"] = path


def registered_python_executable():
    return _state.get("pythonExecutable")


def register_pyqt5(path):
    _state["pyqt5"] = path


def registered_pyqt5():
    return _state.get("pyqt5")


def install_host():
    """Install required components into supported hosts

    An unsupported host will still run, but may encounter issues,
    especially with threading.

    """

    for install in (_install_maya,
                    _install_houdini,
                    _install_nuke,
                    _install_hiero):
        try:
            install()
        except ImportError:
            pass
        else:
            break


def _install_maya():
    """Helper function to Autodesk Maya support"""
    from maya import utils

    def threaded_wrapper(func, *args, **kwargs):
        return utils.executeInMainThreadWithResult(
            func, *args, **kwargs)

    sys.stdout.write("Setting up Pyblish QML in Maya\n")
    register_dispatch_wrapper(threaded_wrapper)

    # Configure GUI
    settings.ContextLabel = "Maya"
    settings.WindowTitle = "Pyblish (Maya)"


def _install_houdini():
    """Helper function to SideFx Houdini support"""
    import hdefereval

    def threaded_wrapper(func, *args, **kwargs):
        return hdefereval.executeInMainThreadWithResult(
            func, *args, **kwargs)

    sys.stdout.write("Setting up Pyblish QML in Houdini\n")
    register_dispatch_wrapper(threaded_wrapper)

    settings.ContextLabel = "Houdini"
    settings.WindowTitle = "Pyblish (Houdini)"


def _install_nuke():
    """Helper function to The Foundry Nuke support"""
    import nuke

    if "--hiero" in nuke.rawArgs or "--studio" in nuke.rawArgs:
        raise ImportError

    def threaded_wrapper(func, *args, **kwargs):
        return nuke.executeInMainThreadWithResult(
            func, args, kwargs)

    sys.stdout.write("Setting up Pyblish QML in Nuke\n")
    register_dispatch_wrapper(threaded_wrapper)

    settings.ContextLabel = "Nuke"
    settings.WindowTitle = "Pyblish (Nuke)"


def _install_hiero():
    """Helper function to The Foundry Hiero support"""
    import hiero
    import nuke

    if "--hiero" not in nuke.rawArgs:
        raise ImportError

    def threaded_wrapper(func, *args, **kwargs):
        return hiero.core.executeInMainThreadWithResult(
            func, args, kwargs)

    sys.stdout.write("Setting up Pyblish QML in Hiero\n")
    register_dispatch_wrapper(threaded_wrapper)

    settings.ContextLabel = "Hiero"
    settings.WindowTitle = "Pyblish (Hiero)"


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
