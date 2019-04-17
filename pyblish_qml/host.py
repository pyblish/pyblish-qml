import os
import sys
import inspect
import logging
import traceback
from functools import wraps

import pyblish.api

from . import ipc, settings, _state
from .vendor.six.moves import queue

MODULE_DIR = os.path.dirname(__file__)
SPLASH_PATH = os.path.join(MODULE_DIR, "splash.png")

log = logging.getLogger(__name__)


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


def install(modal):
    """Perform first time install"""

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


def show(parent=None, targets=[], modal=None, auto_publish=False, auto_validate=False):
    """Attempt to show GUI

    Requires install() to have been run first, and
    a live instance of Pyblish QML in the background.

    Arguments:
        parent (None, optional): Deprecated
        targets (list, optional): Publishing targets
        modal (bool, optional): Block interactions to parent

    """

    # Get modal mode from environment
    if modal is None:
        modal = bool(os.environ.get("PYBLISH_QML_MODAL", False))

    # Automatically install if not already installed.
    install(modal)

    show_settings = settings.to_dict()
    show_settings['autoPublish'] = auto_publish
    show_settings['autoValidate'] = auto_validate

    # Show existing GUI
    if _state.get("currentServer"):
        server = _state["currentServer"]
        proxy = ipc.server.Proxy(server)

        try:
            proxy.show(show_settings)
            return server

        except IOError:
            # The running instance has already been closed.
            _state.pop("currentServer")

    if not host.is_headless():
        host.splash()

    try:
        service = ipc.service.Service()
        server = ipc.server.Server(service, targets=targets, modal=modal)
    except Exception:
        # If for some reason, the GUI fails to show.
        traceback.print_exc()
        return host.desplash()

    proxy = ipc.server.Proxy(server)
    proxy.show(show_settings)

    # Store reference to server for future calls
    _state["currentServer"] = server

    log.info("Success. QML server available as "
             "pyblish_qml.api.current_server()")

    server.listen()

    return server


def proxy_call(func):
    @wraps(func)
    def proxy_call_wrapper(*args, **kwargs):
        # get existing GUI
        if _state.get("currentServer"):
            server = _state["currentServer"]
            proxy = Proxy(server)
            try:
                return func(proxy, *args, **kwargs)
            except IOError:
                # The running instance has already been closed.
                _state.pop("currentServer")
    return proxy_call_wrapper


@proxy_call
def publish(proxy):
    proxy.publish()


@proxy_call
def validate(proxy):
    proxy.validate()


@proxy_call 
def hide(proxy):
    proxy.hide()


@proxy_call
def quit(proxy):
    proxy.quit()


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
                    _install_nukestudio,
                    _install_blender):
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


class Host(object):
    def splash(self):
        pass

    def install(self, host):
        pass

    def uninstall(self):
        pass

    def is_headless(self):
        return True


class QtHost(Host):
    def __init__(self):
        super(QtHost, self).__init__()
        from .vendor.Qt import QtWidgets, QtCore, QtGui

        self.app = QtWidgets.QApplication.instance()
        self.window = None

        self._state = {
            "installed": False,
            "splashWindow": None,
            "eventFilter": None,
        }

        class EventFilter(QtCore.QObject):
            def eventFilter(this, widget, event):
                try:
                    func_name = {
                        QtCore.QEvent.Show: "rise",
                        QtCore.QEvent.Hide: "hide",
                        QtCore.QEvent.WindowActivate: "inFocus",
                        QtCore.QEvent.WindowDeactivate: "outFocus",
                    }[event.type()]
                except KeyError:
                    return False

                server = _state.get("currentServer")
                if server is not None:
                    proxy = ipc.server.Proxy(server)
                    func = getattr(proxy, func_name)

                    try:
                        func()
                        return True

                    except IOError:
                        # The running instance has already been closed.
                        self.uninstall()
                        _state.pop("currentServer")

                return False

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

        self.Splash = Splash
        self.EventFilter = EventFilter

    def splash(self):
        window = self.Splash()
        window.show()

        callback = "pyblishQmlShown", self.desplash
        pyblish.api.register_callback(*callback)

        self._state["splashWindow"] = window

    def desplash(self):
        try:
            self._state.pop("splashWindow").close()

        except (AttributeError, RuntimeError):
            # Splash already closed
            pass

        pyblish.api.deregister_callback("pyblishQmlShown", self.desplash)

    def is_headless(self):
        return (
            # Maya 2017+ in standalone
            not hasattr(self.app, "activeWindow") or

            # Maya 2016-
            not self.app.activeWindow()
        )

    def install(self, host):
        """Setup common to all Qt-based hosts"""
        print("Installing..")
        if self._state["installed"]:
            return

        if self.is_headless():
            log.info("Headless host")
            return

        print("aboutToQuit..")
        self.app.aboutToQuit.connect(self._on_application_quit)

        if host == "Maya":
            print("Maya host..")
            window = {
                widget.objectName(): widget
                for widget in self.app.topLevelWidgets()
            }["MayaWindow"]

        else:
            window = self.find_window()

        # Install event filter
        print("event filter..")
        event_filter = self.EventFilter(window)
        window.installEventFilter(event_filter)

        for signal in SIGNALS_TO_REMOVE_EVENT_FILTER:
            pyblish.api.register_callback(signal, self.uninstall)

        log.info("Installed event filter")

        self.window = window
        self._state["installed"] = True
        self._state["eventFilter"] = event_filter

    def uninstall(self):
        print("uninstalling..")
        if not self._state["installed"]:
            return

        try:
            print("removing eventfilter..")
            self.window.removeEventFilter(self._state["eventFilter"])
        except AttributeError:
            pass

        print("removing callbacks..")
        for signal in SIGNALS_TO_REMOVE_EVENT_FILTER:
            try:
                pyblish.api.deregister_callback(signal, self.uninstall)
            except (KeyError, ValueError):
                pass

        self._state["installed"] = False
        log.info("The eventFilter of pyblish-qml has been removed.")

    def _on_application_quit(self):
        """Automatically kill QML on host exit"""

        try:
            _state["currentServer"].popen.kill()

        except KeyError:
            # No server started
            pass

        except OSError:
            # Already dead
            pass

    def find_window(self):
        """Get top window in host"""
        window = self.app.activeWindow()

        while True:
            parent_window = window.parent()
            if parent_window:
                window = parent_window
            else:
                break

        return window


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


def _common_setup(host_name, threaded_wrapper, use_threaded_wrapper):
    sys.stdout.write("Setting up Pyblish QML in {}\n".format(host_name))

    if use_threaded_wrapper:
        register_dispatch_wrapper(threaded_wrapper)

    host.uninstall()
    host.install(host_name)

    _set_host_label(host_name)


def _install_maya(use_threaded_wrapper):
    """Helper function to Autodesk Maya support"""
    from maya import utils, cmds

    def threaded_wrapper(func, *args, **kwargs):
        return utils.executeInMainThreadWithResult(
            func, *args, **kwargs)

    sys.stdout.write("Setting up Pyblish QML in Maya\n")

    if cmds.about(version=True) == "2018":
        _remove_googleapiclient()

    _common_setup("Maya", threaded_wrapper, use_threaded_wrapper)


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


def _install_blender(use_threaded_wrapper):
    """Blender is a special snowflake

    It doesn't have a mechanism with which to call commands from a thread
    other than the main thread. So what's happening below is we run a polling
    command every 10 milliseconds to see whether QML has any tasks for us.
    If it does, then Blender runs this command (blocking while it does it),
    and passes the result back to QML when ready.

    The consequence of this is that we're polling even though nothing is
    expected to arrive. The cost of polling is expected to be neglible,
    but it's worth keeping in mind and ideally optimise away. E.g. only
    poll when the QML window is actually open.

    """

    import bpy

    qml_to_blender = queue.Queue()
    blender_to_qml = queue.Queue()

    def threaded_wrapper(func, *args, **kwargs):
        qml_to_blender.put((func, args, kwargs))
        return blender_to_qml.get()

    class PyblishQMLOperator(bpy.types.Operator):
        """Operator which runs its self from a timer"""
        bl_idname = "wm.pyblish_qml_timer"
        bl_label = "Pyblish QML Timer Operator"

        _timer = None

        def modal(self, context, event):
            if event.type == 'TIMER':
                try:
                    func, args, kwargs = qml_to_blender.get_nowait()

                except queue.Empty:
                    pass

                else:
                    result = func(*args, **kwargs)
                    blender_to_qml.put(result)

            return {'PASS_THROUGH'}

        def execute(self, context):
            wm = context.window_manager

            # Check the queue ever 10 ms
            # The cost of checking the queue is neglible, but it
            # does mean having Python execute a command all the time,
            # even as the artist is working normally and is nowhere
            # near publishing anything.
            self._timer = wm.event_timer_add(0.01, context.window)

            wm.modal_handler_add(self)
            return {'RUNNING_MODAL'}

        def cancel(self, context):
            wm = context.window_manager
            wm.event_timer_remove(self._timer)

    log.info("Registering Blender + Pyblish operator")
    bpy.utils.register_class(PyblishQMLOperator)

    # Start the timer
    bpy.ops.wm.pyblish_qml_timer()

    # Expose externally, for debugging. It enables you to
    # pause the timer, and add/remove commands by hand.
    _state["QmlToBlenderQueue"] = qml_to_blender
    _state["BlenderToQmlQueue"] = blender_to_qml

    _common_setup("Blender", threaded_wrapper, use_threaded_wrapper)


# Support both Qt and non-Qt host
try:
    host = QtHost()
except ImportError:
    log.info("Non-Qt host found")
    host = Host()
