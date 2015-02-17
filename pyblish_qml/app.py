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
import compat
from vendor import requests


class Rest(object):
    ADDRESS = "http://127.0.0.1:{port}/pyblish/v1{endpoint}"
    PORT = 6000

    def request(self, verb, endpoint, data=None, **kwargs):
        endpoint = self.ADDRESS.format(port=self.PORT,
                                       endpoint=endpoint)
        request = getattr(requests, verb.lower())
        response = request(endpoint, data=data, **kwargs)
        return response


class Controller(QtCore.QObject):
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
        self.toggle_item(self._instance_model, index)

    @QtCore.pyqtSlot(int)
    def togglePlugin(self, index):
        self.toggle_item(self._plugin_model, index)

    @QtCore.pyqtSlot()
    def reset(self):
        self.reset_state()

    @QtCore.pyqtSlot()
    def stop(self):
        self._is_running = False

    def toggle_item(self, model, index):
        qindex = model.createIndex(index, index)
        is_toggled = model.data(qindex, model.IsToggledRole)
        model.setData(index, "isToggled", not is_toggled)

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

        message += "\nPlug-ins:"
        for plugin in plugins:
            message += "\n  - %s" % plugin

        message += "\n"
        self.info.emit(message)

        state = json.dumps({"context": context,
                            "plugins": plugins})

        try:
            response = self._rest.request("POST", "/state",
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

    def __init__(self, host, prefix):
        super(Controller, self).__init__(parent=None)

        self._instances = list()
        self._plugins = list()
        self._system = dict()
        self._has_errors = False
        self._log = util.Log()
        self._rest = Rest()
        self._is_running = False

        self._instance_model = model.InstanceModel()
        self._plugin_model = model.PluginModel()

        self.populate_models()

        self.processed.connect(self.process_handler)
        self.finished.connect(self.finished_handler)

    def start(self):
        """Start processing-loop"""
        def worker():
            response = self._rest.request("POST", "/next")
            while self._is_running and response.status_code == 200:
                self.processed.emit(response.json())
                response = self._rest.request("POST", "/next")
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
                    model_.setData(index, "hasError", True)

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
                model_.setData(index, "isProcessing", False)

    def reset_status(self):
        """Reset progress bars"""
        self._rest.request("POST", "/session").json()
        self._has_errors = False

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

    def populate_models(self):
        with util.Timer("Spent %.2f ms requesting things.."):
            self._rest.request("POST", "/session").json()
            instances = self._rest.request("GET", "/instances").json()
            plugins = self._rest.request("GET", "/plugins").json()
            self._system = self._rest.request("GET", "/application").json()

        defaults = {
            "name": "default",
            "objName": "default",
            "family": "default",
            "families": "default",
            "isToggled": True,
            "active": True,
            "isSelected": False,
            "currentProgress": 0,
            "isProcessing": False,
            "isCompatible": True,
            "hasError": False,
            "hasWarning": False,
            "hasMessage": False,
            "optional": True,
            "errors": list(),
            "warnings": list(),
            "messages": list(),
        }

        for data in instances:
            instance = defaults.copy()
            instance.update(data)
            item = model.Item(**instance)
            item.isToggled = True if item.publish in (True, None) else False
            self._instance_model.addItem(item)

        for data in plugins:
            if data.get("active") is False:
                continue
            plugin = defaults.copy()
            plugin.update(data)
            item = model.Item(**plugin)
            self._plugin_model.addItem(item)


def run_production_app(host, port):
    Rest.PORT = port
    module_dir = os.path.dirname(__file__)

    app = QtGui.QGuiApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(os.path.join(module_dir, "icon.ico")))

    engine = QtQml.QQmlApplicationEngine()

    ctrl = Controller(host, prefix="/pyblish/v1")
    ctx = engine.rootContext()
    ctx.setContextProperty("app", ctrl)

    with util.Timer("Spent %.2f ms building the GUI.."):
        engine.load(os.path.join(module_dir, "qml", "main.qml"))

    window = engine.rootObjects()[0]
    window.show()

    print "Running production app on port: %s" % port
    sys.exit(app.exec_())


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="Python")
    parser.add_argument("--port", type=int, default=6000)

    kwargs = parser.parse_args()

    run_production_app(**kwargs.__dict__)
