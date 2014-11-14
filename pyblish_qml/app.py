"""Python start-up script for QML application

The application registers a Filesystem type into QML
which is then used to display the contents of a directory,
also chosen via QML.

"""

# Standard library
import os
import sys

# Dependencies
from PyQt5 import QtGui, QtCore, QtQml

import pyblish_qml

QML_DIR = os.path.dirname(pyblish_qml.__file__)
QML_DIR = os.path.join(QML_DIR, "qml")


class Connection(QtCore.QObject):
    """Manage endpoint connection"""

    def __init__(self, host, port, parent=None):
        super(Connection, self).__init__(parent)
        self._port = port

    @QtCore.pyqtProperty(int)
    def port(self):
        return self._port


class Window(QtCore.QObject):
    """Manage window"""


def run(host, port=6000):
    app = QtGui.QGuiApplication(sys.argv)

    def finish_load(obj, url):
        if obj is not None:
            obj.show()
            app.exec_()
        else:
            sys.exit()

    connection = Connection(host, port)

    engine = QtQml.QQmlApplicationEngine()
    engine.rootContext().setContextProperty("connection", connection)

    app_path = os.path.join(QML_DIR, "app.qml")

    engine.objectCreated.connect(finish_load)
    engine.load(QtCore.QUrl.fromLocalFile(app_path))


if __name__ == '__main__':
    pyblish_qml.run("Python", 6829, async=True)
    # pyblish_qml.run("Python", 6829)
