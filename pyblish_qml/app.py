"""Application entry-point"""

# Standard library
import os
import sys
import json
import time
import threading

# Dependencies
from PyQt5 import QtCore, QtGui, QtQml

# Local libraries
import util
import rest
import model
import compat
import safety

try:
    import psutil
    HAS_PSUTIL = True
except:
    HAS_PSUTIL = False


MODULE_DIR = os.path.dirname(__file__)
QML_IMPORT_DIR = os.path.join(MODULE_DIR, "qml")
APP_PATH = os.path.join(MODULE_DIR, "qml", "main.qml")
ICON_PATH = os.path.join(MODULE_DIR, "icon.ico")


class CloseEventHandler(QtCore.QObject):
    """Prefer hiding the window, to closing it."""

    def __init__(self, app, parent=None):
        super(CloseEventHandler, self).__init__(parent)
        self.app = app

    def eventFilter(self, obj, event):
        """Allow GUI to be closed upon holding Shift"""
        if event.type() == QtCore.QEvent.Close:
            modifiers = self.app.qapp.queryKeyboardModifiers()
            shift_pressed = QtCore.Qt.ShiftModifier & modifiers

            if not self.app.keep_alive or shift_pressed:
                event.accept()
            else:
                event.ignore()
                self.app.hide()

        return super(CloseEventHandler, self).eventFilter(obj, event)


class Application(QtCore.QObject):
    """Pyblish QML wrapper around QApplication

    Provides production and debug launchers along with controller
    initialisation and orchestration.

    """

    shown = QtCore.pyqtSignal()
    keep_alive = False

    def __init__(self, parent=None):
        super(Application, self).__init__(parent)

        qapp = QtGui.QGuiApplication(sys.argv)
        qapp.setWindowIcon(QtGui.QIcon(ICON_PATH))

        engine = QtQml.QQmlApplicationEngine()
        engine.addImportPath(QML_IMPORT_DIR)

        with util.Timer("Spent %.2f ms building the GUI.."):
            engine.load(APP_PATH)

        window = engine.rootObjects()[0]

        controller = Controller()

        ctx = engine.rootContext()
        ctx.setContextProperty("app", controller)

        self.qapp = qapp
        self.window = window
        self.engine = engine
        self.controller = controller

        self.shown.connect(self.on_shown)

        self.__close_event_handler = CloseEventHandler(self)
        window.installEventFilter(self.__close_event_handler)

    def show(self):
        """Display GUI

        Once the QML interface has been loaded, use this
        to display it.

        """

        window = self.window

        if not window.isVisible():
            self.controller.reload()

        window.requestActivate()
        window.showNormal()

        if os.name == "nt":
            # Work-around for window appearing behind
            # other windows upon being shown once hidden.
            previous_flags = window.flags()
            window.setFlags(previous_flags | QtCore.Qt.WindowStaysOnTopHint)
            window.setFlags(previous_flags)

    def hide(self):
        """Hide GUI

        Process remains active and may be shown via a call to `show()`

        """

        self.window.hide()

    def on_shown(self):
        """Handle show events"""

        self.show()

    def exec_(self):
        """Wrapper around QApplication.exec_()"""

        return self.qapp.exec_()

    def listen(self):
        """Listen on incoming requests from host

        Usage:
            >> from pyblish_endpoint import client
            >> client.request("show")

        """

        def worker():
            while True:
                resp = rest.request("POST", "/dispatch").json()

                if resp.get("show"):
                    self.shown.emit()
                else:
                    self.controller.info.emit(
                        "Unhandled incoming message: %s" % resp)

                # NOTE(marcus): If we don't sleep, signals get trapped
                # TODO(marcus): Find a way around that.
                time.sleep(0.1)

        thread = threading.Thread(target=worker, name="listener")
        thread.daemon = True
        thread.start()

        util.echo("Listening..")

    def run_production(self):
        """Launch production-version of GUI

        A production-version is dependent on an externally
        available instance of Pyblish Endpoint at rest.PORT

        """

        util.echo("Running production app on port: %s" % rest.PORT)

        self.show()
        self.listen()

    def run_debug(self):
        """Launch debug-version of GUI

        The debug-version does not require an independent
        instance of Pyblish Endpoint, but rather instantiates
        a mock to simulate it's responses.

        See mocking.py for more details.

        """

        import mocking
        import pyblish_endpoint.server

        endpoint_app, _ = pyblish_endpoint.server.create_app()
        endpoint_app.config["TESTING"] = True
        endpoint_client = endpoint_app.test_client()
        endpoint_client.testing = True

        rest.MOCK = endpoint_client

        Service = mocking.MockService
        Service.SLEEP_DURATION = 0.5
        Service.PERFORMANCE = Service.FAST
        pyblish_endpoint.service.register_service(Service, force=True)

        util.echo("Running debug app on port: %s" % rest.PORT)

        self.show()


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

    called = QtCore.pyqtSignal(QtCore.QVariant, arguments=["result"])

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
        self.__toggle_item(self._instance_model, index)

    @QtCore.pyqtSlot(int, result=QtCore.QVariant)
    def pluginData(self, index):
        return self.__item_data(self._plugin_model, index)

    @QtCore.pyqtSlot(int, result=QtCore.QVariant)
    def instanceData(self, index):
        return self.__item_data(self._instance_model, index)

    @QtCore.pyqtSlot(int)
    def togglePlugin(self, index):
        model = self._plugin_model
        item = model.itemFromIndex(index)

        if item.optional:
            self.__toggle_item(self._plugin_model, index)
        else:
            self.error.emit("Plug-in is mandatory")

    @QtCore.pyqtSlot()
    def reset(self):
        self.reload()

    @QtCore.pyqtSlot()
    def stop(self):
        self._is_running = False

    def __item_data(self, model, index):
        """Return item data as dict"""
        item = model.itemFromIndex(index)
        return item.__dict__

    def __toggle_item(self, model, index):
        if self._is_running:
            self.error.emit("Cannot untick while publishing")
        else:
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
        self.__start()

    @QtCore.pyqtProperty(QtCore.QObject)
    def log(self):
        return self._log

    def __init__(self, parent=None):
        """
        Attributes:
            _instances
            _plugins
            _state: The current state in use during processing

        """

        super(Controller, self).__init__(parent)

        self._instances = list()
        self._plugins = list()
        self._system = dict()
        self._has_errors = False
        self._log = util.Log()
        self._is_running = False
        self._state = dict()

        self._instance_model = model.InstanceModel()
        self._plugin_model = model.PluginModel()

        self.finished.connect(self.__on_finished)

    def reload(self):
        with util.Timer("Spent %.2f ms requesting data host.."):
            rest.request("POST", "/session")
            system = rest.request("GET", "/application").json()
            instances = rest.request("GET", "/instances").json()
            plugins = rest.request("GET", "/plugins").json()

        # Remove existing items from model
        self._instance_model.reset()
        self._plugin_model.reset()

        for data in instances:
            item = model.Item(**data)
            item.isToggled = True if item.publish in (True, None) else False
            self._instance_model.addItem(item)

        for data in plugins:
            if data.get("active") is False:
                continue

            if data.get("type") == "Selector":
                continue

            item = model.Item(**data)
            self._plugin_model.addItem(item)

        self._system = system

    def __start(self):
        """Start processing-loop"""

        def worker():
            response = rest.request("POST", "/next")
            while self._is_running and response.status_code == 200:
                self.__on_processed(response.json())
                self.processed.emit(response.json())
                response = rest.request("POST", "/next")
            self.finished.emit()

        self.__reset_state()

        thread = threading.Thread(target=worker, name="publisher")
        thread.daemon = True
        thread.start()

    def __on_finished(self):
        self.__reset_status()

    def __on_processed(self, data):
        self.__update_instances(data)
        self.__update_plugins(data)

    def __update_instances(self, data):
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
                    model_.setData(index, "succeeded", True)

            else:
                model_.setData(index, "isProcessing", False)

    def __update_plugins(self, data):
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

    def __reset_status(self):
        """Reset progress bars"""
        rest.request("POST", "/session").json()
        self._has_errors = False
        self._is_running = False

        for model_ in (self._instance_model, self._plugin_model):
            for item in model_.items:
                index = model_.itemIndex(item)
                model_.setData(index, "isProcessing", False)
                model_.setData(index, "currentProgress", 0)

    def __reset_state(self):
        """Reset data from last publish"""
        for model_ in (self._instance_model, self._plugin_model):
            for item in model_.items:
                index = model_.itemIndex(item)
                model_.setData(index, "hasError", False)
                model_.setData(index, "succeeded", False)


def main(port, pid=None, preload=False, validate=True):

    try:
        safety.validate()
    except Exception as e:
        util.echo(
            """Could not start application due to a misconfigured environment.

Pass validate=False to pyblish_qml.app:main
in order to bypass validation.

See below message for more information.
"""
        )

        util.echo("Environment:")
        util.echo("-" * 32)

        for key, value in safety.stats.iteritems():
            util.echo("%s = %s" % (key, value))

        util.echo()
        util.echo("Error:")
        util.echo("-" * 32)
        util.echo(e)
        return 255

    rest.PORT = port

    with util.Timer("Spent %.2f ms creating the application"):
        app = Application()

        if preload:
            app.keep_alive = True
            app.listen()

        elif port == 6000:
            app.run_debug()

        else:
            app.keep_alive = True
            app.run_production()

    if pid and HAS_PSUTIL:
        util.echo("%s parented to pid: %s" % (os.getpid(), pid))

        def monitor():
            psutil.Process(pid).wait()
            util.echo("Force quitting.. (parent killed)")
            os._exit(1)

        t = threading.Thread(target=monitor, name="psutilMonitor")
        t.daemon = True
        t.start()

    return app.exec_()


def cli():
    """Pyblish QML command-line interface

    Arguments:
        port (int): Port at which to communicate with Pyblish Endpoint
        pid (int, optional): Process ID of parent process
        preload (bool, optional): Whether or not to pre-load the GUI

    """

    import argparse

    compat.main()

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="Python")  # deprecated
    parser.add_argument("--port", type=int, default=6000)
    parser.add_argument("--pid", type=int, default=None)
    parser.add_argument("--preload", action="store_true")

    kwargs = parser.parse_args()
    port = kwargs.port
    pid = kwargs.pid
    preload = kwargs.preload

    return main(port, pid, preload)


if __name__ == "__main__":
    sys.exit(cli())
