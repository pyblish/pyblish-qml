import os
import time
import logging

from PyQt5 import QtCore


def echo(text=""):
    print text


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
