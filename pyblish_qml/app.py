"""Application entry-point"""

# Standard library
import os
import sys
import json
import threading

# Dependencies
from PyQt5 import QtGui, QtCore, QtQml

# Local libraries
import util
import model
import rest
import compat
import mock


class Controller(QtCore.QObject):
    """Handle events coming from QML

    Attributes:
        error (str): [Signal] Outgoing error
        info (str): [Signal] Outgoing message
        processed (dict): [Signal] Outgoing state from host per process
        finished: [Signal] Upon finished publish

    """

    error = QtCore.pyqtSignal(str, arguments=["message"])
    info = QtCore.pyqtSignal(str, arguments=["message"])
    processed = QtCore.pyqtSignal(QtCore.QVariant, arguments=["data"])
    finished = QtCore.pyqtSignal()

    @QtCore.pyqtProperty(QtCore.QVariant)
    def instances(self):
        return self._instances

    @QtCore.pyqtProperty(QtCore.QVariant)
    def plugins(self):
        return self._plugins

    @QtCore.pyqtProperty(QtCore.QVariant, constant=True)
    def pluginModel(self):
        return self._plugin_model

    @QtCore.pyqtProperty(QtCore.QVariant, constant=True)
    def instanceModel(self):
        return self._instance_model

    @QtCore.pyqtProperty(QtCore.QVariant, constant=True)
    def system(self):
        return self._system

    @QtCore.pyqtSlot(int)
    def toggleInstance(self, index):
        self._toggle_item(self._instance_model, index)

    @QtCore.pyqtSlot(int, result=QtCore.QVariant)
    def pluginData(self, index):
        return self._item_data(self._plugin_model, index)

    @QtCore.pyqtSlot(int, result=QtCore.QVariant)
    def instanceData(self, index):
        return self._item_data(self._instance_model, index)

    @QtCore.pyqtSlot(int)
    def togglePlugin(self, index):
        model = self._plugin_model
        item = model.itemFromIndex(index)

        if item.optional:
            self._toggle_item(self._plugin_model, index)
        else:
            self.error.emit("Plug-in is mandatory")

    @QtCore.pyqtSlot()
    def reset(self):
        self.reset_state()

    @QtCore.pyqtSlot()
    def stop(self):
        self._is_running = False

    def _item_data(self, model, index):
        """Return item data as dict"""
        item = model.itemFromIndex(index)
        return item.__dict__

    def _toggle_item(self, model, index):
        if self._is_running:
            self.error.emit("Cannot untick while publishing")
            return

        item = model.itemFromIndex(index)
        model.setData(index, "isToggled", not item.isToggled)

    @QtCore.pyqtSlot()
    def publish(self):
        context = list()
        for instance in self._instance_model.serialized:
            if instance.get("isToggled"):
                context.append(instance["name"])

        plugins = list()
        for plugin in self._plugin_model.serialized:
            if plugin.get("isToggled"):
                plugins.append(plugin["name"])

        if not all([context, plugins]):
            msg = "Must specify an instance and plug-in"
            self.finished.emit()
            self.error.emit(msg)
            self.log.error(msg)
            return

        message = "Instances:"
        for instance in context:
            message += "\n  - %s" % instance

        message += "\n\nPlug-ins:"
        for plugin in plugins:
            message += "\n  - %s" % plugin

        message += "\n"
        self.info.emit(message)

        state = json.dumps({"context": context,
                            "plugins": plugins})

        try:
            response = rest.request("POST", "/state",
                                    data={"state": state})
            if response.status_code != 200:
                raise Exception(response.get("message") or "An error occurred")

        except Exception as e:
            self.error.emit(e.msg)
            self.log.error(e.msg)
            return

        self._is_running = True
        self.start()

    @QtCore.pyqtProperty(QtCore.QObject)
    def log(self):
        return self._log

    def __init__(self):
        """

        Attributes:
            _instances
            _plugins
            _state: The current state in use during processing

        """

        super(Controller, self).__init__(parent=None)

        self._instances = list()
        self._plugins = list()
        self._system = dict()
        self._has_errors = False
        self._log = util.Log()
        self._is_running = False
        self._state = dict()

        self._instance_model = model.InstanceModel()
        self._plugin_model = model.PluginModel()

        self.populate_models()

        self.processed.connect(self.process_handler)
        self.finished.connect(self.finished_handler)

    def start(self):
        """Start processing-loop"""

        def worker():
            response = rest.request("POST", "/next")
            while self._is_running and response.status_code == 200:
                self.processed.emit(response.json())
                response = rest.request("POST", "/next")
            self.finished.emit()

        self.reset_state()

        thread = threading.Thread(target=worker)
        thread.daemon = True
        thread.start()

    def finished_handler(self):
        self.reset_status()

    def process_handler(self, data):
        self.update_instances(data)
        self.update_plugins(data)

    def update_instances(self, data):
        model_ = self._instance_model
        for item in model_.items:
            index = model_.itemIndex(item)
            current_item = data.get("instance")

            if current_item == item.name:
                model_.setData(index, "isProcessing", True)
                model_.setData(index, "currentProgress", 1)

                if data.get("error"):
                    print "ERROR: %s" % current_item
                    model_.setData(index, "hasError", True)
                else:
                    model_.setData(index, "succeeded", True)

            else:
                model_.setData(index, "isProcessing", False)

    def update_plugins(self, data):
        model_ = self._plugin_model
        for item in model_.items:
            index = model_.itemIndex(item)
            current_item = data.get("plugin")

            if current_item == item.name:
                if self._has_errors:
                    if item.type == "Extractor":
                        self.info.emit("Stopped due to failed vaildation")
                        self._is_running = False
                        return

                model_.setData(index, "isProcessing", True)
                model_.setData(index, "currentProgress", 1)

                if data.get("error"):
                    model_.setData(index, "hasError", True)
                    self._has_errors = True
                else:
                    model_.setData(index, "succeeded", True)

            else:
                model_.setData(index, "isProcessing", False)

    def reset_status(self):
        """Reset progress bars"""
        rest.request("POST", "/session").json()
        self._has_errors = False
        self._is_running = False

        for model_ in (self._instance_model, self._plugin_model):
            for item in model_.items:
                index = model_.itemIndex(item)
                model_.setData(index, "isProcessing", False)
                model_.setData(index, "currentProgress", 0)

    def reset_state(self):
        """Reset data from last publish"""
        for model_ in (self._instance_model, self._plugin_model):
            for item in model_.items:
                index = model_.itemIndex(item)
                model_.setData(index, "hasError", False)
                model_.setData(index, "succeeded", False)

    def populate_models(self):
        with util.Timer("Spent %.2f ms requesting things.."):
            rest.request("POST", "/session").json()
            instances = rest.request("GET", "/instances").json()
            plugins = rest.request("GET", "/plugins").json()
            self._system = rest.request("GET", "/application").json()

        for data in instances:
            item = model.Item(**data)
            item.isToggled = True if item.publish in (True, None) else False
            self._instance_model.addItem(item)

        for data in plugins:
            if data.get("active") is False:
                continue

            item = model.Item(**data)
            self._plugin_model.addItem(item)


def run_production_app(port):
    rest.PORT = port

    print "Running production app on port: %s" % rest.PORT
    return _run_app()


def run_debug_app():
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
    return _run_app()


def _run_app():
    module_dir = os.path.dirname(__file__)
    qml_import_dir = os.path.join(module_dir, "qml")
    app_path = os.path.join(module_dir, "qml", "main.qml")

    app = QtGui.QGuiApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(os.path.join(module_dir, "icon.ico")))

    engine = QtQml.QQmlApplicationEngine()
    engine.addImportPath(qml_import_dir)
    engine.objectCreated.connect(_object_created_handler)

    ctrl = Controller()
    ctx = engine.rootContext()
    ctx.setContextProperty("app", ctrl)

    with util.Timer("Spent %.2f ms building the GUI.."):
        engine.load(app_path)

    sys.exit(app.exec_())


def _object_created_handler(obj, url):
    """Show the Window as soon as it has been created"""
    if obj is not None:
        obj.show()
    else:
        sys.exit()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="Python")
    parser.add_argument("--port", type=int, default=6000)

    kwargs = parser.parse_args()

    if kwargs.port is not 6000:
        run_production_app(kwargs.port)
    else:
        run_debug_app()
