"""Application entry-point"""

# Standard library
import os
import sys
import json

# Dependencies
from PyQt5 import QtGui, QtCore, QtQml

# Local libraries
import lib
import rest
import model


class Controller(QtCore.QObject):
    error = QtCore.pyqtSignal(str, arguments=["message"])
    info = QtCore.pyqtSignal(str, arguments=["message"])
    processed = QtCore.pyqtSignal(QtCore.QVariant, arguments=["data"])

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

    def toggle_item(self, model, index):
        qindex = model.createIndex(index, index)
        is_toggled = model.data(qindex, model.IsToggledRole)
        model.setData(index, "isToggled", not is_toggled)

    @QtCore.pyqtSlot()
    def publish(self):
        context = list()
        for instance in self._instance_model.serialized:
            if not instance["isToggled"]:
                continue
            context.append(instance["name"])

        plugins = list()
        for plugin in self._plugin_model.serialized:
            if not plugin["isToggled"]:
                continue
            plugins.append(plugin["name"])

        if not all([context, plugins]):
            msg = "Must specify an instance and plug-in"
            self.processed.emit({"finished": True, "message": msg})
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
            rest.post_state(state)
        except Exception as e:
            self.error.emit(e.msg)
            self.log.error(e.msg)
            return

        rest.post_next(signal=self.processed)

    @QtCore.pyqtProperty(QtCore.QObject)
    def log(self):
        return self._log

    def __init__(self, host, prefix):
        super(Controller, self).__init__(parent=None)

        self._instances = list()
        self._plugins = list()
        self._system = dict()
        self._log = lib.Log()

        self._instance_model = model.InstanceModel()
        self._plugin_model = model.PluginModel()

        self.load()

        self.processed.connect(self.processHandler)

    def processHandler(self, data):
        if data.get("finished"):
            for type, model in (("instance", self._instance_model),
                                ("plugin", self._plugin_model)):

                for item in model.items:
                    index = model.itemIndex(item)
                    model.setData(index, "isProcessing", False)
                    model.setData(index, "currentProgress", 0)

        else:
            for type, model in (("instance", self._instance_model),
                                ("plugin", self._plugin_model)):

                item = data.get(type)
                index = model.itemIndexByName(item)

                if index:
                    model.setData(index, "isProcessing", True)
                    model.setData(index, "currentProgress", 1)

    def load(self):
        with lib.Timer("Spent %.2f ms requesting things.."):
            rest.request("POST", "/session").json()
            instances = rest.request("GET", "/instances").json()
            plugins = rest.request("GET", "/plugins").json()
            self._system = rest.request("GET", "/application").json()

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
            item.isToggled = True if item.publish else False
            self._instance_model.addItem(item)

        for data in plugins:
            if data.get("active") is False:
                continue
            plugin = defaults.copy()
            plugin.update(data)
            item = model.Item(**plugin)
            self._plugin_model.addItem(item)


def run_production_app(host, port):
    print "Running production app on port: %s" % port
    rest.PORT = port

    app = QtGui.QGuiApplication(sys.argv)

    engine = QtQml.QQmlApplicationEngine()

    ctrl = Controller(host, prefix="/pyblish/v1")
    ctx = engine.rootContext()
    ctx.setContextProperty("app", ctrl)

    module_dir = os.path.dirname(__file__)

    with lib.Timer("Spent %.2f ms building the GUI.."):
        engine.load(os.path.join(module_dir, "qml", "main.qml"))

    window = engine.rootObjects()[0]
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="Python")
    parser.add_argument("--port", type=int, default=6000)

    kwargs = parser.parse_args()

    run_production_app(**kwargs.__dict__)
