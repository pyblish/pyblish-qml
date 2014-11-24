"""Python start-up script for QML application

The application registers a Filesystem type into QML
which is then used to display the contents of a directory,
also chosen via QML.

"""

# Standard library
import os
import sys
import json
import logging
import threading

# Dependencies
from PyQt5 import QtGui, QtCore, QtQml

import pyblish_qml
import pyblish_endpoint.server
import pyblish_endpoint.service

QML_DIR = os.path.dirname(pyblish_qml.__file__)
QML_DIR = os.path.join(QML_DIR, "qml")
APP_PATH = os.path.join(QML_DIR, "app.qml")

log = logging.getLogger("qml")

# Context properties
pyqt = None
connection = None


class PyQt(QtCore.QObject):
    """Expose common PyQt functionality"""

    NoModifier = QtCore.pyqtProperty(int)(lambda self: QtCore.Qt.NoModifier)
    ShiftModifier = QtCore.pyqtProperty(int)(lambda self: QtCore.Qt.ShiftModifier)
    ControlModifier = QtCore.pyqtProperty(int)(lambda self: QtCore.Qt.ControlModifier)
    AltModifier = QtCore.pyqtProperty(int)(lambda self: QtCore.Qt.AltModifier)

    @QtCore.pyqtSlot(result=int)
    def queryKeyboardModifiers(self):
        return QtGui.QGuiApplication.queryKeyboardModifiers()


class Connection(QtCore.QObject):
    """Manage endpoint connection"""

    def __init__(self, host, port, prefix, parent=None):
        super(Connection, self).__init__(parent)
        self._port = port
        self._host = host
        self._prefix = prefix

    @QtCore.pyqtProperty(int)
    def port(self):
        return self._port

    @QtCore.pyqtProperty(str)
    def host(self):
        return self._host

    @QtCore.pyqtProperty(str)
    def prefix(self):
        return self._prefix


class MockHTTPRequest(QtCore.QObject):
    requested = QtCore.pyqtSignal(QtCore.QVariant)
    client = None

    @QtCore.pyqtSlot(str, str, QtCore.QVariant)
    def request(self, verb, endpoint, data=None):

        def thread():
            response = self._request(verb, endpoint, data)
            self.requested.emit(response)

        t = threading.Thread(target=thread)
        t.daemon = True
        t.start()

    def _request(self, verb, endpoint, data=None):
        """Flask test-client with PyQt slot

        Arguments:
            verb (str): How to request
            endpoint (str): Where to request
            data (dict, optional): Data to POST

        """

        log.debug("%s %s (data=%s)" % (verb, endpoint, data))
        func = getattr(self.client, verb.lower())
        response = func(endpoint, data=data)
        assert response.headers["Content-Type"] == "application/json"

        response_data = json.loads(response.data)
        return response_data


def create_app(host, port=6000):
    app = QtGui.QGuiApplication(sys.argv)

    def finish_load(obj, url):
        if obj is not None:
            obj.show()
            app.exec_()
        else:
            sys.exit()

    engine = QtQml.QQmlApplicationEngine()
    engine.objectCreated.connect(finish_load)

    global pyqt
    global connection

    pyqt = PyQt()
    connection = Connection(host, port, prefix="/pyblish/v1")

    engine.rootContext().setContextProperty("PyQt", pyqt)
    engine.rootContext().setContextProperty("Connection", connection)

    return engine


def run_production_app(host, port):
    print "Running production app on port: %s" % port
    engine = create_app(host, port)

    engine.load(QtCore.QUrl.fromLocalFile(APP_PATH))


def run_debug_app():
    """Run app with mocked Flask client

    The client emulates a host using the MockService used
    in Endpoint tests.

    """

    engine = create_app(host="Mock", port=0)

    app, api = pyblish_endpoint.server.create_app()

    client = app.test_client()
    client.testing = True

    Service = pyblish_endpoint.service.MockService
    Service.PERFORMANCE = Service.SLOW
    pyblish_endpoint.service.register_service(Service,
                                              force=True)

    MockHTTPRequest.client = client

    QtQml.qmlRegisterType(MockHTTPRequest, 'Python', 1, 0, 'MockHTTPRequest')
    engine.load(QtCore.QUrl.fromLocalFile(APP_PATH))


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="Python")
    parser.add_argument("--port", type=int, default=0)

    kwargs = parser.parse_args()

    if kwargs.port == 0:
        run_debug_app()
    else:
        run_production_app(**kwargs.__dict__)
