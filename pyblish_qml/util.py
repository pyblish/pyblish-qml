import os
import time
import logging

from PyQt5 import QtCore

_timers = {}
_invokes = []


def echo(text=""):
    print text


def timer(name):
    if name in _timers:
        return
    _timers[name] = time.time()


def timer_end(name, format=None):
    _time = _timers.pop(name, None)
    format = format or name + ": %.3f ms"
    if _time is not None:
        echo(format % (time.time() - _time))


def invoke(target, callback=None):
    """Perform operation in thread with callback

    Instances are cached until finished, at which point
    they are garbage collected. If we didn't do this,
    Python would step in and garbage collect the thread
    before having had time to finish, resulting in an
    exception.

    Arguments:
        target (callable): Method or function to call
        callback (callable, optional): Method or function to call
            once `target` has finished.

    Returns:
        None

    """

    obj = _Invoke(target, callback)
    obj.finished.connect(lambda: _invoke_cleanup(obj))
    obj.start()
    _invokes.append(obj)


class _Invoke(QtCore.QThread):

    done = QtCore.pyqtSignal(QtCore.QVariant, arguments=["result"])

    def __init__(self, target, callback=None):
        super(_Invoke, self).__init__()

        self.target = target

        if callback:
            connection = QtCore.Qt.BlockingQueuedConnection
            self.done.connect(callback, type=connection)

    def run(self, *args, **kwargs):
        result = self.target(*args, **kwargs)
        self.done.emit(result)


def _invoke_cleanup(obj):
    _invokes.remove(obj)


class Timer(object):
    """Time operations using this context manager

    Arguments:
        format (str): Optional format for output. Defaults to "%.3f ms"

    """

    def __init__(self, format=None):
        self._format = format or "%.3f ms"

    def __enter__(self):
        self._time = time.time()

    def __exit__(self, type, value, tb):
        print self._format % ((time.time() - self._time) * 1000)


class Log(QtCore.QObject):
    """Expose Python's logging mechanism to QML"""

    def __init__(self, name="qml", parent=None):
        super(Log, self).__init__(parent)
        self.log = logging.getLogger(name)

        formatter = logging.Formatter("%(levelname)s %(message)s")
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self.log.addHandler(handler)

        # self.log.setLevel(logging.INFO)
        self.log.setLevel(logging.DEBUG)
        self.log.propagate = True

    @QtCore.pyqtSlot(str)
    def debug(self, msg):
        self.log.debug(msg)

    @QtCore.pyqtSlot(str)
    def info(self, msg):
        self.log.info(msg)

    @QtCore.pyqtSlot(str)
    def warning(self, msg):
        self.log.warning(msg)

    @QtCore.pyqtSlot(str)
    def error(self, msg):
        self.log.error(msg)


def where(program):
    """Parse PATH for executables

    Windows note:
        PATHEXT yields possible suffixes, such as .exe, .bat and .cmd

    Usage:
        >>> where("python")
        c:\python27\python.exe

    """

    suffixes = [""]

    try:
        # Append Windows suffixes, such as .exe, .bat and .cmd
        suffixes.extend(os.environ.get("PATHEXT").split(os.pathsep))
    except:
        pass

    for path in os.environ["PATH"].split(os.pathsep):

        # A path may be empty.
        if not path:
            continue

        for suffix in suffixes:
            full_path = os.path.join(path, program + suffix)
            if os.path.isfile(full_path):
                return full_path
