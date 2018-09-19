import os
import sys
import json
import threading
import subprocess
import time
import ctypes
from ctypes import pythonapi as cpyapi

from .. import _state
from ..vendor import six
from ..vendor.Qt import QtWidgets, QtCore

CREATE_NO_WINDOW = 0x08000000
IS_WIN32 = sys.platform == "win32"


SIGNALS_TO_CLOSE_VESSEL = (
    "pyblishQmlClose",
    "pyblishQmlCloseForced",
)


def default_wrapper(func, *args, **kwargs):
    return func(*args, **kwargs)


class FosterVessel(QtWidgets.QDialog):
    """Container window for pyblish-qml App in child process
    """

    def __init__(self, proxy):
        super(FosterVessel, self).__init__(_state.get("vesselParent"))

        # (NOTE) Although minimizing this vesselized dialog works well on
        #   Windows 10, but QQuickView window did not hide well on Windows 7.
        #   Other platform not tested yet, disable it for now.
        #
        # Enable maximize for app, minimize disabled
        self.setWindowFlags(QtCore.Qt.Window |
                            QtCore.Qt.WindowCloseButtonHint |
                            QtCore.Qt.WindowMaximizeButtonHint)

        self._winId = winIdFixed(self.winId())

        self.resize(1, 1)

        self.proxy = proxy
        self.close_lock = True

    def closeEvent(self, event):
        if self.close_lock:
            self.proxy.quit()
            event.ignore()
        else:
            event.accept()

    def resizeEvent(self, event):
        self.proxy._dispatch("resize", args=[self.width(), self.height()])


class MockFosterVessel(object):
    """We don't create widget without QApp, we mock one"""
    _winId = close_lock = None
    show = hide = close = lambda _: None


class Proxy(object):
    """Speak to child process and control the vessel (window container)"""

    def __init__(self, server):
        import pyblish.api

        self.popen = server.popen
        self.foster = server.foster
        self.foster_fixed = server.foster_fixed

        self.vessel = FosterVessel(self) if self.foster else MockFosterVessel()
        self._winId = self.vessel._winId

        server.proxy = self

        def close_vessel():
            self.vessel.close_lock = False
            self.vessel.close()

            for signal in SIGNALS_TO_CLOSE_VESSEL:
                try:
                    pyblish.api.deregister_callback(signal, self.close_vessel)
                except (KeyError, ValueError):
                    pass

        self.close_vessel = close_vessel

        for signal in SIGNALS_TO_CLOSE_VESSEL:
            pyblish.api.register_callback(signal, self.close_vessel)

        self._alive()

    def show(self, settings=None):
        """Show the GUI

        Arguments:
            settings (optional, dict): Client settings

        """
        if self.foster_fixed:
            self.vessel.show()
        return self._dispatch("show", args=[settings or {},
                                            self._winId,
                                            self.foster_fixed])

    def hide(self):
        """Hide the GUI"""
        success = self._dispatch("hide")
        self.vessel.hide()
        return success

    def quit(self):
        """Ask the GUI to quit"""
        self._dispatch("quit")

    def rise(self):
        """Rise GUI from hidden"""
        self.vessel.show()
        return self._dispatch("rise")

    def inFocus(self):
        """Set GUI on-top flag"""
        return self._dispatch("inFocus")

    def outFocus(self):
        """Remove GUI on-top flag"""
        return self._dispatch("outFocus")

    def kill(self):
        """Forcefully destroy the process"""
        self.popen.kill()

    def detach(self):
        self.vessel.setWindowOpacity(0)  # avoid hide window anim
        self.vessel.hide()
        self._dispatch("host_detach")

    def attach(self, x, y, w, h):
        self.vessel.show()
        self.vessel.setGeometry(x, y, w, h)
        self.vessel.setWindowOpacity(1)
        self._dispatch("host_attach")

    def popup(self, alert):
        # No hijack keyboard focus
        if not self.foster_fixed:
            QtWidgets.QApplication.setActiveWindow(self.vessel)
        # Plus alert
        if alert:
            QtWidgets.QApplication.alert(self.vessel.parent(), 0)

    def publish(self):
        return self._dispatch("publish")

    def validate(self):
        return self._dispatch("validate")

    def _alive(self):
        """Send pulse to child process

        Child process will run forever if parent process encounter such
        failure that not able to kill child process.

        This inform child process that server is still running and child
        process will auto kill itself after server stop sending pulse
        message.

        """

        def _pulse():
            start_time = time.time()

            while True:
                data = json.dumps({"header": "pyblish-qml:server.pulse"})
                if not self._flush(data):
                    break

                # Send pulse every 5 seconds
                time.sleep(5.0 - ((time.time() - start_time) % 5.0))

        thread = threading.Thread(target=_pulse)
        thread.daemon = True
        thread.start()

    def _dispatch(self, func, args=None):
        data = json.dumps(
            {
                "header": "pyblish-qml:popen.parent",
                "payload": {
                    "name": func,
                    "args": args or list(),
                }
            }
        )

        return self._flush(data)

    def _flush(self, data):
        if six.PY3:
            data = data.encode("ascii")

        try:
            self.popen.stdin.write(data + b"\n")
            self.popen.stdin.flush()
        except IOError:
            # subprocess closed
            self.close_vessel()
        else:
            return True


class Server(object):
    """A subprocess server

    This server relies on stdout and stdin for interprocess communication.

    Arguments:
        service (service.Service): Dispatch requests to this service
        python (str, optional): Absolute path to Python executable
        pyqt5 (str, optional): Absolute path to PyQt5
        targets (list, optional): Publishing targets, e.g. `ftrack`
        modal (bool, optional): Block interactions to parent
        foster (bool, optional): GUI become a real child of the parent process
        foster_fixed (bool, optional): GUI always remain inside the parent

    """

    def __init__(self,
                 service,
                 python=None,
                 pyqt5=None,
                 targets=[],
                 modal=False,
                 foster=False,
                 foster_fixed=False):
        super(Server, self).__init__()
        self.service = service
        self.listening = False

        self.proxy = None

        # Store modal state
        self.modal = modal

        self.foster = foster
        self.foster_fixed = foster_fixed

        # The server may be run within Maya or some other host,
        # in which case we refer to it as running embedded.
        is_embedded = os.path.split(sys.executable)[-1].lower() != "python.exe"

        python = python or find_python()
        pyqt5 = pyqt5 or find_pyqt5(python)

        print("Using Python @ '%s'" % python)
        print("Using PyQt5 @ '%s'" % pyqt5)

        # Maintain the absolute minimum of environment variables,
        # to avoid issues on invalid types.
        if IS_WIN32:
            environ = {
                key: os.getenv(key)
                for key in ("USERNAME",
                            "SYSTEMROOT",
                            "PYTHONPATH",
                            "PATH")
                if os.getenv(key)
            }
        else:
            # OSX and Linux users are left to fend for themselves.
            environ = os.environ.copy()

        # Append PyQt5 to existing PYTHONPATH, if available
        environ["PYTHONPATH"] = os.pathsep.join(
            path for path in [os.getenv("PYTHONPATH"), pyqt5]
            if path is not None
        )

        # Protect against an erroneous parent environment
        # The environment passed to subprocess is inherited from
        # its parent, but the parent may - at run time - have
        # made the environment invalid. For example, a unicode
        # key or value in `os.environ` is not a valid environment.
        if not all(isinstance(key, str) for key in environ):
            print("One or more of your environment variable "
                  "keys are not <str>")

            for key in os.environ:
                if not isinstance(key, str):
                    print("- %s is not <str>" % key)

        if not all(isinstance(key, str) for key in environ.values()):
            print("One or more of your environment "
                  "variable values are not <str>")

            for key, value in os.environ.items():
                if not isinstance(value, str):
                    print("- Value of %s=%s is not <str>" % (key, value))

        kwargs = dict(args=[
            python, "-u", "-m", "pyblish_qml",

            # Indicate that this is a child of the parent process,
            # and that it should expect to speak with the parent
            "--aschild"],

            # Any path other than where the host was launched from
            # to prevent accidental pickup of e.g. PyQt5 binaries.
            cwd=os.path.dirname(__file__),

            env=environ,

            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

        if IS_WIN32 and is_embedded:
            # This will prevent an embedded Python
            # from opening an external terminal window.
            kwargs["creationflags"] = CREATE_NO_WINDOW

        # If no targets are passed to pyblish-qml, we assume that we want the
        # default target and the registered targets. This is to facilitate
        # getting all plugins on pyblish_qml.show().
        import pyblish.api
        if not targets:
            targets = ["default"] + pyblish.api.registered_targets()
        print("Targets: {0}".format(", ".join(targets)))

        kwargs["args"].append("--targets")
        kwargs["args"].extend(targets)

        self.popen = subprocess.Popen(**kwargs)

    def stop(self):
        try:
            return self.popen.kill()
        except OSError as e:
            # Assume process is already dead
            print(e)

    def wait(self):
        return self.popen.wait()

    def listen(self):
        """Listen to both stdout and stderr

        We'll want messages of a particular origin and format to
        cause QML to perform some action. Other messages are simply
        forwarded, as they are expected to be plain print or error messages.

        """

        def _listen():
            """This runs in a thread"""
            for line in iter(self.popen.stdout.readline, b""):

                if six.PY3:
                    line = line.decode("utf8")

                try:
                    response = json.loads(line)

                except Exception:
                    # This must be a regular message.
                    sys.stdout.write(line)

                else:
                    if response.get("header") == "pyblish-qml:popen.request":
                        payload = response["payload"]
                        args = payload["args"]

                        func_name = payload["name"]

                        # self.service have no access to proxy object, so
                        # this `if` statement is needed
                        if func_name in ("detach", "attach", "popup"):
                            getattr(self.proxy, func_name)(*args)
                            result = None

                        elif func_name in ("emit",):
                            # Avoid main thread hang
                            result = getattr(self.service, func_name)(*args)

                        else:
                            wrapper = _state.get("dispatchWrapper",
                                                 default_wrapper)

                            func = getattr(self.service, func_name)
                            result = wrapper(func, *args)  # block..

                        # Note(marcus): This is where we wait for the host to
                        # finish. Technically, we could kill the GUI at this
                        # point which would make the following commands throw
                        # an exception. However, no host is capable of kill
                        # the GUI whilst running a command. The host is locked
                        # until finished, which means we are guaranteed to
                        # always respond.

                        data = json.dumps({
                            "header": "pyblish-qml:popen.response",
                            "payload": result
                        })

                        if six.PY3:
                            data = data.encode("ascii")

                        try:
                            self.popen.stdin.write(data + b"\n")
                            self.popen.stdin.flush()
                        except IOError:
                            # subprocess closed
                            return

                    else:
                        # In the off chance that a message
                        # was successfully decoded as JSON,
                        # but *wasn't* a request, just print it.
                        sys.stdout.write(line)

        if not self.listening:
            if self.modal:
                _listen()
            else:
                thread = threading.Thread(target=_listen)
                thread.daemon = True
                thread.start()

            self.listening = True


def find_python():
    """Search for Python automatically"""
    python = (
        _state.get("pythonExecutable") or

        # Support for multiple executables.
        next((
            exe for exe in
            os.getenv("PYBLISH_QML_PYTHON_EXECUTABLE", "").split(os.pathsep)
            if os.path.isfile(exe)), None
        ) or

        # Search PATH for executables.
        which("python") or
        which("python3")
    )

    if not python or not os.path.isfile(python):
        raise ValueError("Could not locate Python executable.")

    return python


def find_pyqt5(python):
    """Search for PyQt5 automatically"""
    pyqt5 = (
        _state.get("pyqt5") or
        os.getenv("PYBLISH_QML_PYQT5")
    )

    return pyqt5


def which(program):
    """Locate `program` in PATH

    Arguments:
        program (str): Name of program, e.g. "python"

    """

    def is_exe(fpath):
        if os.path.isfile(fpath) and os.access(fpath, os.X_OK):
            return True
        return False

    for path in os.environ["PATH"].split(os.pathsep):
        for ext in os.getenv("PATHEXT", "").split(os.pathsep):
            fname = program + ext.lower()
            abspath = os.path.join(path.strip('"'), fname)

            if is_exe(abspath):
                return abspath

    return None


def winIdFixed(winId):
    # PySide bug: QWidget.winId() returns <PyCObject object at 0x02FD8788>,
    # there is no easy way to convert it to int.
    try:
        return int(winId)
    except Exception:
        if sys.version_info[0] == 2:
            cpyapi.PyCObject_AsVoidPtr.restype = ctypes.c_void_p
            cpyapi.PyCObject_AsVoidPtr.argtypes = [ctypes.py_object]

            return cpyapi.PyCObject_AsVoidPtr(winId)

        elif sys.version_info[0] == 3:
            cpyapi.PyCapsule_GetPointer.restype = ctypes.c_void_p
            cpyapi.PyCapsule_GetPointer.argtypes = [ctypes.py_object]

            return cpyapi.PyCapsule_GetPointer(winId, None)
