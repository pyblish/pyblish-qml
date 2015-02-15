import time
import logging

from PyQt5 import QtCore


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
