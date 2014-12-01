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
APP_PATH = os.path.join(QML_DIR, "qml", "app.qml")

log = logging.getLogger("qml")


class PyQt(QtCore.QObject):
    """Expose common PyQt functionality"""

    NoModifier = QtCore.pyqtProperty(int)(lambda self: QtCore.Qt.NoModifier)
    ShiftModifier = QtCore.pyqtProperty(int)(lambda self: QtCore.Qt.ShiftModifier)
    ControlModifier = QtCore.pyqtProperty(int)(lambda self: QtCore.Qt.ControlModifier)
    AltModifier = QtCore.pyqtProperty(int)(lambda self: QtCore.Qt.AltModifier)

    @QtCore.pyqtSlot(result=int)
    def queryKeyboardModifiers(self):
        return QtGui.QGuiApplication.queryKeyboardModifiers()


class Log(QtCore.QObject):
    """Expose Python's logging mechanism to QML"""

    def __init__(self, name="qml", parent=None):
        super(Log, self).__init__(parent)
        self.log = logging.getLogger(name)
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


class Application(object):
    """Main Application

    This object wraps common QML functionality in order to
    prevent, mainly context properties, from getting garbage
    collected after having been set.

    """

    def __init__(self, host, port, prefix):
        app = QtGui.QGuiApplication(sys.argv)

        engine = QtQml.QQmlApplicationEngine()
        engine.objectCreated.connect(self.load_finished_handler)

        self.app = app
        self.engine = engine
        self.context_properties = []
        self.registered_types = []

        log = Log()
        pyqt = PyQt()
        connection = Connection(host, port, prefix)

        self.set_context_property("Log", log)
        self.set_context_property("PyQt", pyqt)
        self.set_context_property("Connection", connection)

        self.setup_log()

    def setup_log(self):
        formatter = logging.Formatter("%(levelname)s %(message)s")
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        log.addHandler(handler)
        log.setLevel(logging.INFO)
        # log.setLevel(logging.DEBUG)

    def load(self, path):
        qurl = QtCore.QUrl.fromLocalFile(APP_PATH)
        self.engine.load(qurl)

    def load_finished_handler(self, obj, url):
        if obj is not None:
            obj.show()
            self.app.exec_()
        else:
            sys.exit()

    def register_type(self, obj, uri, version_major, version_minor, qml_name):
        QtQml.qmlRegisterType(obj, uri, version_major, version_minor, qml_name)
        self.registered_types.append(obj)

    def set_context_property(self, name, value):
        context = self.engine.rootContext()
        context.setContextProperty(name, value)
        self.context_properties.append(value)


def run_production_app(host, port):
    print "Running production app on port: %s" % port
    app = Application(host, port, prefix="/pyblish/v1")
    app.load(APP_PATH)


def run_debug_app():
    """Run app with mocked Flask client

    The client emulates a host using the MockService used
    in Endpoint tests.

    """

    app = Application(host="Mock", port=0, prefix="/pyblish/v1")

    endpoint_app, _ = pyblish_endpoint.server.create_app()
    endpoint_app.config["TESTING"] = True
    endpoint_client = endpoint_app.test_client()
    endpoint_client.testing = True

    Service = pyblish_endpoint.service.MockService
    Service.PERFORMANCE = Service.MODERATE
    pyblish_endpoint.service.register_service(Service,
                                              force=True)
    MockHTTPRequest.client = endpoint_client
    app.register_type(MockHTTPRequest, 'Python', 1, 0, 'MockHTTPRequest')
    app.load(APP_PATH)


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
