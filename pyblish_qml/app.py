"""Application entry-point"""

# Standard library
import os
import sys
import time

# Dependencies
from PyQt5 import QtGui, QtQml

# Local libraries
import util
import rest
import mock
import compat
import controller


class Application(object):
    MODULE_DIR = os.path.dirname(__file__)
    QML_IMPORT_DIR = os.path.join(MODULE_DIR, "qml")
    APP_PATH = os.path.join(MODULE_DIR, "qml", "main.qml")
    ICON_PATH = os.path.join(MODULE_DIR, "icon.ico")

    def __init__(self, port=6000):
        qapp = QtGui.QGuiApplication(sys.argv)
        qapp.setWindowIcon(QtGui.QIcon(self.ICON_PATH))

        engine = QtQml.QQmlApplicationEngine()
        engine.addImportPath(self.QML_IMPORT_DIR)
        engine.objectCreated.connect(self._object_created_handler)

        ctrl = controller.Controller()

        ctx = engine.rootContext()
        ctx.setContextProperty("app", ctrl)

        self.engine = engine
        self.qapp = qapp
        self.port = port
        self.ctrl = ctrl

    def init(self):
        self.ctrl.async_init()

    def run_production(self):
        print "Running production app on port: %s" % rest.PORT
        rest.PORT = self.port
        return self._run()

    def run_debug(self):
        import pyblish_endpoint.server

        endpoint_app, _ = pyblish_endpoint.server.create_app()
        endpoint_app.config["TESTING"] = True
        endpoint_client = endpoint_app.test_client()
        endpoint_client.testing = True

        rest.MOCK = endpoint_client

        Service = mock.MockService
        Service.SLEEP_DURATION = 0.5
        Service.PERFORMANCE = Service.FAST
        pyblish_endpoint.service.register_service(Service, force=True)

        print "Running debug app on port: %s" % rest.PORT
        return self._run()

    def _run(self):
        with util.Timer("Spent %.2f ms building the GUI.."):
            self.engine.load(self.APP_PATH)

    def _object_created_handler(self, obj, url):
        """Show the Window as soon as it has been created"""
        if obj is not None:
            obj.show()
            self.init()
            sys.exit(self.qapp.exec_())
        else:
            sys.exit()


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="Python")
    parser.add_argument("--port", type=int, default=6000)

    kwargs = parser.parse_args()

    app = Application(kwargs.port)

    if kwargs.port is 6000:
        app.run_debug()
    else:
        app.run_production()


if __name__ == "__main__":
    main()
