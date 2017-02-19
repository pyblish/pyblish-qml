import os
import sys
import json
import threading
import subprocess

from .. import _state


def default_wrapper(func, *args, **kwargs):
    return func(*args, **kwargs)


class Proxy(object):
    """Speak to child process"""

    def __init__(self, popen):
        self.popen = popen

    def show(self, settings=None):
        """Show the GUI

        Arguments:
            settings (optional, dict): Client settings

        """

        self._dispatch("show")

    def hide(self):
        """Hide the GUI"""
        self._dispatch("hide")

    def quit(self):
        """Ask the GUI to quit"""
        self._dispatch("quit")

    def kill(self):
        """Forcefully destroy the process, this does not return"""
        self.popen.kill()

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

        self.popen.stdin.write(data + "\n")
        self.popen.stdin.flush()


class Server(object):
    """A subprocess server

    This server relies on stdout and stdin for interprocess communication.

    """

    def __init__(self, service, python=None, pyqt5=None):
        super(Server, self).__init__()
        self.service = service
        self.listening = False

        python = python or find_python()
        pyqt5 = pyqt5 or find_pyqt5(python)

        print("Using Python @ '%s'" % python)
        print("Using PyQt5 @ '%s'" % pyqt5)

        self.popen = subprocess.Popen(
            [python, "-u", "-m", "pyblish_qml", "--aschild"],
            env=dict(os.environ, **{

                # Hosts naturally assume their Python distribution
                # is the only one. We'll have to explicitly say
                # to use ours instead.
                "PYTHONHOME": os.path.split(python)[0],

                # Include PyQt5 for this session, without interfering
                # with the PYTHONPATH of the parent process.
                "PYTHONPATH": os.pathsep.join(path for path in [
                    os.getenv("PYTHONPATH"),
                    pyqt5,
                ] if path is not None)
            }),

            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,

            # CREATE_NO_WINDOW
            # This is only relevant on Windows, but does
            # no harm on other OSs.
            creationflags=0x08000000
        )

        self.listen()

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
                try:
                    response = json.loads(line)

                except Exception:
                    # This must be a regular message.
                    sys.stdout.write(line)

                else:
                    if response["header"] == "pyblish-qml:popen.request":
                        payload = response["payload"]
                        args = payload["args"]

                        wrapper = _state.get("dispatchWrapper",
                                             default_wrapper)

                        func = getattr(self.service, payload["name"])
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

                        self.popen.stdin.write(data + "\n")
                        self.popen.stdin.flush()

                    else:
                        # In the off chance that a message
                        # was successfully decoded as JSON,
                        # but *wasn't* a request, just print it.
                        sys.stdout.write(line)

        if not self.listening:
            thread = threading.Thread(target=_listen)
            thread.daemon = True
            thread.start()

            self.listening = True


def find_python():
    """Search for Python automatically"""
    python = (
        _state.get("pythonExecutable") or
        os.getenv("PYBLISH_QML_PYTHON_EXECUTABLE") or
        which("python") or
        which("python3")
    )

    if not python:
        raise ValueError("Could not locate Python executable.")

    return python


def find_pyqt5(python):
    """Search for PyQt5 automatically"""
    pyqt5 = (
        _state.get("pyqt5") or
        os.getenv("PYBLISH_QML_PYQT5")
    )

    if pyqt5 is None:
        try:
            cmd = "import imp;print(imp.find_module('PyQt5')[1])"
            pyqt5 = subprocess.check_output([python, "-c", cmd]).rstrip()
        except subprocess.CalledProcessError:
            raise ValueError("Could not locate PyQt5")

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
