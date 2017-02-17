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

        python = (
            python or
            _state.get("pythonExecutable") or
            which("python") or
            which("python3")
        )

        if python is None:
            raise ValueError("Could not locate Python executable.")

        pyqt5 = pyqt5 or _state.get("pyqt5")

        if pyqt5 is None:
            try:
                cmd = "import imp;print(imp.find_module('PyQt5')[1])"
                pyqt5 = subprocess.check_output([python, "-c", cmd]).rstrip()
            except subprocess.CalledProcessError:
                raise ValueError("Could not locate PyQt5")

        print("Found Python @ '%s'" % python)
        print("Found PyQt5 @ '%s'" % pyqt5)

        CREATE_NO_WINDOW = 0x08000000

        self.popen = subprocess.Popen(
            [python, "-u", "-m", "pyblish_qml", "--aschild"],
            env=dict(os.environ, **{
                "PYTHONHOME": os.path.split(python)[0],
                "PYTHONPATH": os.pathsep.join([
                    os.getenv("PYTHONPATH", ""),
                    pyqt5,
                ])
            }),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,

            # This is only relevant on Windows, but does
            # no harm on other OSs.
            creationflags=CREATE_NO_WINDOW
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

        for channel in (self.popen.stdout, self.popen.stderr):
            thread = threading.Thread(
                target=listen,
                args=[
                    channel,
                    self.popen.stdin,
                    self.service
                ]
            )

            thread.daemon = True
            thread.start()


def listen(transmitter, receiver, service):
    """Make requests to `transmitter` and receive responses via `receiver`

    Arguments:
        transmitter (file): A file-like object, such as sys.stdout
        receiver (file): A file-like object, such as sys.stdin
        service (object): Requests are made to this object

    """

    for line in iter(transmitter.readline, b""):
        try:
            response = json.loads(line)

        except Exception:
            # This must be a regular message.
            sys.stdout.write(line)

        else:
            if response["header"] == "pyblish-qml:popen.request":
                payload = response["payload"]
                args = payload["args"]

                wrapper = _state.get("dispatchWrapper", default_wrapper)

                func = getattr(service, payload["name"])
                result = wrapper(func, *args)

                data = json.dumps({
                    "header": "pyblish-qml:popen.response",
                    "payload": result
                })

                receiver.write(data + "\n")
                receiver.flush()

            else:
                sys.stdout.write(line)


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
