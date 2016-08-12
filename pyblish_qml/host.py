import os
import sys
import time
import socket
import inspect
import traceback
import threading

# Python 2 and 3 compatibility
from .vendor.six.moves import xmlrpc_client as xmlrpclib

import pyblish.api

from . import rpc, settings


self = sys.modules[__name__]
self.ACTIVE_HOST_PORT = None
self.ACTIVE_PROXY = None
self.ACTIVE_HOST_NAME = None


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

    rpc.server.dispatch_wrapper = wrapper


def deregister_dispatch_wrapper():
    rpc.server.dispatch_wrapper = None


def dispatch_wrapper():
    return rpc.server.dispatch_wrapper


def install(initial_port=9001):
    """Perform first time install

    Attributes:
        initial_port (int, optional): Port from which to start
            looking for available ports, defaults to 9001

    """

    if self.ACTIVE_HOST_PORT is not None:
        uninstall()

    install_host()
    install_callbacks()

    try:
        # In case QML is live and well, ask it
        # for the next available initial_port number.
        self.ACTIVE_PROXY = proxy()
        self.ACTIVE_HOST_PORT = self.ACTIVE_PROXY.find_available_port(
            initial_port)

    except (socket.timeout, socket.error):
        raise socket.error(
            "Is Pyblish QML running?\n\n"

            "This GUI requires a separate, standalone process to be running\n"
            "in the background in order to make use of it from within {host}\n"
            "Make sure to run python -m pyblish_qml prior to showing it from\n"
            "from {host}.\n\n"

            "See the documentation for further information.\n"
            "- https://github.com/pyblish/pyblish-qml\n\n#"
            .format(
                host=self.ACTIVE_HOST_NAME or "a host")
        )

    os.environ["PYBLISH_CLIENT_PORT"] = str(self.ACTIVE_HOST_PORT)

    try:
        _serve()

    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        message = "".join(traceback.format_exception(
            exc_type, exc_value, exc_traceback))
        sys.stderr.write(message)
        sys.stderr.write("Setup failed..\n")


def uninstall():
    """Kill server and clean up traces of Pyblish QML in this process"""
    if self.ACTIVE_PROXY is None:
        return

    del self.ACTIVE_PROXY

    self.ACTIVE_HOST_PORT = None
    self.ACTIVE_PROXY = None

    uninstall_callbacks()
    uninstall_server()

    sys.stdout.write("Pyblish QML shutdown successful.\n")


def show():
    """Attempt to show GUI

    Requires install() to have been run first, and
    a live instance of Pyblish QML in the background.

    """

    if not self.ACTIVE_HOST_PORT:
        sys.stdout.write("Running install() for the first time.\n")
        install()

    if self.ACTIVE_PROXY is None:
        self.ACTIVE_PROXY = proxy()

    try:
        self.ACTIVE_PROXY.show(
            self.ACTIVE_HOST_PORT,
            settings.to_dict()
        )

    except (socket.error, socket.timeout):
        raise socket.error(
            "Communication problem.\n"
            "\n"
            "Hello? Is it me you're looking for?\n"
            "\n"
            "This problem typically occurs when Pyblish QML \n"
            "was running, but isn't anymore.\n"
            "\n"
            "To start it again, go to any terminal any type:\n"
            "$ python -m pyblish_qml"
        )


def install_callbacks():
    pyblish.api.register_callback("instanceToggled", _toggle_instance)


def uninstall_callbacks():
    pyblish.api.deregister_callback("instanceToggled", _toggle_instance)


def uninstall_server():
    rpc.server.kill()


def _serve():
    """Start XML-RPC server

    This is the entrypoint towards which the remote Pyblish QML instance
    communicates.

    """

    assert self.ACTIVE_HOST_PORT

    def server():
        """Provide QML with a friend to speak with"""
        self.server = rpc.server.start_production_server(self.ACTIVE_HOST_PORT)

    def heartbeat_emitter():
        """Let QML know we're still here"""
        p = proxy()

        while True:
            try:
                p.heartbeat(self.ACTIVE_HOST_PORT)
                time.sleep(1)
            except (socket.error, socket.timeout):
                pass

    for worker in (server, heartbeat_emitter):
        t = threading.Thread(target=worker, name=worker.__name__)
        t.daemon = True
        t.start()

    sys.stdout.write("Server running @ %i\n" % self.ACTIVE_HOST_PORT)

    return self.ACTIVE_HOST_PORT


def _toggle_instance(instance, new_value, old_value):
    """Alter instance upon visually toggling instance"""
    instance.data["publish"] = new_value


def proxy(timeout=5):
    """Return proxy at default location of Pyblish QML"""
    return xmlrpclib.ServerProxy(
        "http://127.0.0.1:9090",
        allow_none=True)


def install_host():
    """Install required components into supported hosts

    An unsupported host will still run, but may encounter issues,
    especially with threading.

    """

    for install in (_install_maya,
                    _install_houdini,
                    _install_nuke):
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

    self.ACTIVE_HOST_NAME = "Maya"


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

    self.ACTIVE_HOST_NAME = "Houdini"


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

    self.ACTIVE_HOST_NAME = "Nuke"


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

    self.ACTIVE_HOST_NAME = "Hiero"
