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

    def _wrapper(func, *args, **kwargs):
        """Exception handling"""
        try:
            return wrapper(func, *args, **kwargs)
        except Exception as e:
            # Kill subprocess
            _state["currentServer"].stop()
            traceback.print_exc()
            raise e

    _state["dispatchWrapper"] = _wrapper


def deregister_dispatch_wrapper():
    _state.pop("dispatchWrapper")


def dispatch_wrapper():
    return _state.get("dispatchWrapper")


def current_server():
    return _state.get("currentServer")


def install(modal, foster):
    """Perform first time install

    Attributes:
        initial_port (int, optional): Port from which to start
            looking for available ports, defaults to 9001

    """

    if _state.get("installed"):
        sys.stdout.write("Already installed, uninstalling..\n")
        uninstall()

    use_threaded_wrapper = not modal

    install_callbacks()
    install_host(use_threaded_wrapper)

    _state["installed"] = True


def uninstall():
    """Clean up traces of Pyblish QML"""
    uninstall_callbacks()
    sys.stdout.write("Pyblish QML shutdown successful.\n")


def _is_headless():
    app = QtWidgets.QApplication.instance()
    return (
        # Maya 2017+ in standalone
        not hasattr(app, "activeWindow") or

        # Maya 2016-
        not app.activeWindow()
    )


def _fosterable(foster, modal):
    if foster is None:
        # Get foster mode from environment
        foster = bool(os.environ.get("PYBLISH_QML_FOSTER", False))

    if foster:
        if modal or _is_headless():
            print("Foster disabled due to Modal is on or in headless mode.")
            return False

        print("Foster on.")
        return True

    else:
        return False


def _foster_fixed(foster):
    if not foster:
        return False

    value = os.environ.get("PYBLISH_QML_FOSTER_FIXED", "").lower()
    return value in ("true", "yes", "1") or QtCore.qVersion()[0] == "4"


def show(parent=None, targets=[], modal=None, foster=None):
    """Attempt to show GUI

    Requires install() to have been run first, and
    a live instance of Pyblish QML in the background.

    Arguments:
        parent (None, optional): Deprecated
        targets (list, optional): Publishing targets
        modal (bool, optional): Block interactions to parent
        foster (bool, optional): Become a real child of the parent process

    """

    # Get modal mode from environment
    if modal is None:
        modal = bool(os.environ.get("PYBLISH_QML_MODAL", False))

    is_headless = _is_headless()

    foster = _fosterable(foster, modal)
    foster_fixed = _foster_fixed(foster)

    # Automatically install if not already installed.
    if not _state.get("installed"):
        install(modal, foster)

    # Show existing GUI
    if _state.get("currentServer"):
        server = _state["currentServer"]
        proxy = server.proxy or ipc.server.Proxy(server)

        if proxy.show(settings.to_dict()):
            return server

        else:
            # The running instance has already been closed.
            _state.pop("currentServer")

    if not is_headless:
        # mayapy would have a QtGui.QGuiApplication
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
    else:
        def on_shown():
            pass

    try:
        service = ipc.service.Service()
        server = ipc.server.Server(service,
                                   targets=targets,
                                   modal=modal,
                                   foster=foster,
                                   foster_fixed=foster_fixed)
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

    # Install eventFilter if not exists one
    install_event_filter()

    server.listen()

    return server


def publish():
    # get existing GUI
    if _state.get("currentServer"):
        server = _state["currentServer"]
        proxy = server.proxy or ipc.server.Proxy(server)

        if not proxy.publish():
            # The running instance has already been closed.
            _state.pop("currentServer")


def validate():
    # get existing GUI
    if _state.get("currentServer"):
        server = _state["currentServer"]
        proxy = server.proxy or ipc.server.Proxy(server)

        if not proxy.validate():
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


def install_host(use_threaded_wrapper):
    """Install required components into supported hosts

    An unsupported host will still run, but may encounter issues,
    especially with threading.

    """

    for install in (_install_maya,
                    _install_houdini,
                    _install_nuke,
                    _install_nukeassist,
                    _install_hiero,
                    _install_nukestudio):
        try:
            install(use_threaded_wrapper)
        except ImportError:
            pass
        else:
            break


SIGNALS_TO_REMOVE_EVENT_FILTER = (
    "pyblishQmlClose",
    "pyblishQmlCloseForced",
)


def remove_event_filter():
    event_filter = _state.get("eventFilter")
    if isinstance(event_filter, QtCore.QObject):

        # (NOTE) Should remove from the QApp instance which originally
        #        installed to.
        #        This will not work:
        #        `QApplication.instance().removeEventFilter(event_filter)`
        #
        event_filter.parent().removeEventFilter(event_filter)
        del _state["eventFilter"]

        for signal in SIGNALS_TO_REMOVE_EVENT_FILTER:
            try:
                pyblish.api.deregister_callback(signal, remove_event_filter)
            except (KeyError, ValueError):
                pass

        print("The eventFilter of pyblish-qml has been removed.")


def install_event_filter():

    main_window = _state.get("vesselParent")
    if main_window is None:
        print("Main window not found, event filter did not install.")
        return

    event_filter = _state.get("eventFilter")
    if isinstance(event_filter, QtCore.QObject):
        print("Event filter exists.")
        return
    else:
        event_filter = HostEventFilter(main_window)

    try:
        main_window.installEventFilter(event_filter)
    except Exception as e:
        print("An error has occurred during event filter's installation.")
        print(e)
    else:
        _state["eventFilter"] = event_filter

        for signal in SIGNALS_TO_REMOVE_EVENT_FILTER:
            pyblish.api.register_callback(signal, remove_event_filter)

        print("Event filter has been installed.")


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


class HostEventFilter(QtWidgets.QWidget):
    """Connect some event from host to QML

    Host will connect following event to QML:
    QEvent.Show                -> rise QML
    QEvent.Hide                -> hide QML
    QEvent.WindowActivate      -> set QML on top
    QEvent.WindowDeactivate    -> remove QML on top
    """

    eventList = {
        QtCore.QEvent.Show: "rise",
        QtCore.QEvent.Hide: "hide",
        QtCore.QEvent.WindowActivate: "inFocus",
        QtCore.QEvent.WindowDeactivate: "outFocus",
    }

    def eventFilter(self, widget, event):

        try:
            func_name = self.eventList[event.type()]
        except KeyError:
            return False

        server = _state.get("currentServer")
        proxy = server.proxy if server else None

        try:
            func = getattr(proxy, func_name)
        except AttributeError:
            # proxy is None, or does not have the function
            return False

        connected = func()

        if connected is not True:
            # The running instance has already been closed.
            remove_event_filter()

        return True


def _acquire_host_main_window(app):

    # Get top window in host
    _window = app.activeWindow()
    while True:
        parent_window = _window.parent()
        if parent_window:
            _window = parent_window
        else:
            break

    _state["vesselParent"] = _window


def _set_host_label(host_name):
    if settings.ContextLabel == settings.ContextLabelDefault:
        settings.ContextLabel = host_name
    if settings.WindowTitle == settings.WindowTitleDefault:
        settings.WindowTitle = "Pyblish ({})".format(host_name)


def _remove_googleapiclient():
    """Check if the compatibility must be maintained

    The Maya 2018 version tries to import the `http` module from
    Maya2018\plug-ins\MASH\scripts\googleapiclient\http.py in stead of the
    module from six.py. This import conflict causes a crash Avalon's publisher.
    This is due to Autodesk adding paths to the PYTHONPATH environment variable
    which contain modules instead of only packages.
    """

    keyword = "googleapiclient"

    # reconstruct python paths
    python_paths = os.environ["PYTHONPATH"].split(os.pathsep)
    paths = [path for path in python_paths if keyword not in path]
    os.environ["PYTHONPATH"] = os.pathsep.join(paths)


def _install_maya(use_threaded_wrapper):
    """Helper function to Autodesk Maya support"""
    from maya import utils, cmds

    def threaded_wrapper(func, *args, **kwargs):
        return utils.executeInMainThreadWithResult(
            func, *args, **kwargs)

    sys.stdout.write("Setting up Pyblish QML in Maya\n")

    if use_threaded_wrapper:
        register_dispatch_wrapper(threaded_wrapper)

    if cmds.about(version=True) == "2018":
        _remove_googleapiclient()

    app = QtWidgets.QApplication.instance()

    if not _is_headless():
        # mayapy would have a QtGui.QGuiApplication
        app.aboutToQuit.connect(_on_application_quit)

        # acquire Maya's main window
        _state["vesselParent"] = {
            widget.objectName(): widget
            for widget in QtWidgets.QApplication.topLevelWidgets()
        }["MayaWindow"]

    _set_host_label("Maya")


def _common_setup(host_name, threaded_wrapper, use_threaded_wrapper):

    sys.stdout.write("Setting up Pyblish QML in {}\n".format(host_name))

    if use_threaded_wrapper:
        register_dispatch_wrapper(threaded_wrapper)

    app = QtWidgets.QApplication.instance()
    app.aboutToQuit.connect(_on_application_quit)
    _acquire_host_main_window(app)

    _set_host_label(host_name)


def _install_houdini(use_threaded_wrapper):
    """Helper function to SideFx Houdini support"""
    import hdefereval

    def threaded_wrapper(func, *args, **kwargs):
        return hdefereval.executeInMainThreadWithResult(
            func, *args, **kwargs)

    _common_setup("Houdini", threaded_wrapper, use_threaded_wrapper)


def _install_nuke(use_threaded_wrapper):
    """Helper function to The Foundry Nuke support"""
    import nuke

    not_nuke_launch = (
        "--hiero" in nuke.rawArgs or
        "--studio" in nuke.rawArgs or
        "--nukeassist" in nuke.rawArgs
    )
    if not_nuke_launch:
        raise ImportError

    def threaded_wrapper(func, *args, **kwargs):
        return nuke.executeInMainThreadWithResult(
            func, args, kwargs)

    _common_setup("Nuke", threaded_wrapper, use_threaded_wrapper)


def _install_nukeassist(use_threaded_wrapper):
    """Helper function to The Foundry NukeAssist support"""
    import nuke

    if "--nukeassist" not in nuke.rawArgs:
        raise ImportError

    def threaded_wrapper(func, *args, **kwargs):
        return nuke.executeInMainThreadWithResult(
            func, args, kwargs)

    _common_setup("NukeAssist", threaded_wrapper, use_threaded_wrapper)


def _install_hiero(use_threaded_wrapper):
    """Helper function to The Foundry Hiero support"""
    import hiero
    import nuke

    if "--hiero" not in nuke.rawArgs:
        raise ImportError

    def threaded_wrapper(func, *args, **kwargs):
        return hiero.core.executeInMainThreadWithResult(
            func, args, kwargs)

    _common_setup("Hiero", threaded_wrapper, use_threaded_wrapper)


def _install_nukestudio(use_threaded_wrapper):
    """Helper function to The Foundry Hiero support"""
    import nuke

    if "--studio" not in nuke.rawArgs:
        raise ImportError

    def threaded_wrapper(func, *args, **kwargs):
        return nuke.executeInMainThreadWithResult(
            func, args, kwargs)

    _common_setup("NukeStudio", threaded_wrapper, use_threaded_wrapper)


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
