"""Application entry-point"""

# Standard library
import os
import sys
import json
import time
import logging
import threading

# Dependencies
from PyQt5 import QtCore, QtGui, QtQml

# Local libraries
import util
import models
import compat

# Vendor libraries
from vendor import requests

MODULE_DIR = os.path.dirname(__file__)
QML_IMPORT_DIR = os.path.join(MODULE_DIR, "qml")
APP_PATH = os.path.join(MODULE_DIR, "qml", "main.qml")
ICON_PATH = os.path.join(MODULE_DIR, "icon.ico")

REST_ADDRESS = "http://127.0.0.1:{port}/pyblish/v1{endpoint}"
REST_PORT = 6000


def request(verb, endpoint, data=None, **kwargs):
    """Make a request to Endpoint

    Attributes:
        verb (str): GET, PUT, POST or DELETE request
        endpoint (str): Tail of endpoint; e.g. /client
        data (dict, optional): Data used for POST or PUT requests

    """

    endpoint = REST_ADDRESS.format(port=REST_PORT, endpoint=endpoint)

    request = getattr(requests, verb.lower())
    response = request(endpoint, data=data, **kwargs)

    return response


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

            if shift_pressed:
                util.echo("Shift pressed, accepting close event")
                event.accept()

            elif not self.app.keep_alive:
                util.echo("Not keeping alive, accepting close event")
                event.accept()
            else:
                util.echo("Ignoring close event")
                event.ignore()
                self.app.hide()

        return super(CloseEventHandler, self).eventFilter(obj, event)


class Application(QtCore.QObject):
    """Pyblish QML wrapper around QApplication

    Provides production and debug launchers along with controller
    initialisation and orchestration.

    """

    shown = QtCore.pyqtSignal()
    server_unresponsive = QtCore.pyqtSignal()
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
        self.server_unresponsive.connect(self.on_server_unresponsive)

        self.__close_event_handler = CloseEventHandler(self)
        window.installEventFilter(self.__close_event_handler)

    def show(self):
        """Display GUI

        Once the QML interface has been loaded, use this
        to display it.

        """

        window = self.window

        if not window.isVisible():
            self.controller.reset()

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

        Process remains active and may be shown
        via a call to `show()`

        """

        self.window.hide()

    def quit(self):
        """Quit the application"""
        sys.exit()

    def on_shown(self):
        """Handle show events"""
        self.show()

    def on_server_unresponsive(self):
        """Handle server unresponsive events"""

        util.echo("Server unresponsive; shutting down")

        self.quit()

    def exec_(self):
        """Wrapper around QApplication.exec_()"""

        return self.qapp.exec_()

    def listen(self):
        """Listen on incoming messages from host

        Two types of messages are handled here;
            1. Heartbeat
            2. Not heartbeat

        In the event of a heartbeat not being received on-time,
        the application is notified that the server might be
        unresponsive.

        Any other event is handled separately.

        Usage:
            >> from pyblish_endpoint import client
            >> client.request("show")  # Show a hidden GUI
            >> client.request("close")  # Close GUI permanently
            >> client.request("kill")  # Close GUI forcefully (careful)

        """

        timer = {"time": 0,
                 "count": 0,
                 "interval": 1,
                 "intervals_before_death": 2}

        def message_monitor():
            while True:
                try:
                    response = request("POST", "/client").json()
                except Exception as e:
                    util.echo(getattr(e, "msg", str(e)))
                    self.server_unresponsive.emit()
                    break

                message = response.get("message")

                if message == "heartbeat":
                    timer["value"] = time.time()
                    timer["count"] += 1

                elif message == "show":
                    self.shown.emit()

                elif message == "close":
                    self.quit()

                elif message == "kill":
                    util.echo(
                        "Kill message received from "
                        "server, shutting down NOW!")
                    os._exit(1)

                else:
                    self.controller.info.emit(
                        "Unhandled incoming message: \"%s\""
                        % message)

                # NOTE(marcus): If we don't sleep, signals get trapped
                # TODO(marcus): Find a way around that.
                time.sleep(0.1)

        def heartbeat_monitor():
            while True:
                time.sleep(timer["interval"])
                if timer["time"] > (timer["interval"] *
                                    timer["intervals_before_death"]):
                    util.echo("Timer interval elapsed")
                    self.server_unresponsive.emit()

        for thread in (message_monitor, heartbeat_monitor):
            thread = threading.Thread(target=thread, name=thread.__name__)
            thread.daemon = True
            thread.start()


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

    about_to_process = QtCore.pyqtSignal(QtCore.QVariant, arguments=["pair"])
    processed = QtCore.pyqtSignal(QtCore.QVariant, arguments=["data"])

    finished = QtCore.pyqtSignal()
    saved = QtCore.pyqtSignal()
    selected = QtCore.pyqtSignal()

    # Thread-safe signals
    about_to_process_blocking = QtCore.pyqtSignal(QtCore.QVariant, arguments=["pair"])
    processed_blocking = QtCore.pyqtSignal(QtCore.QVariant, arguments=["data"])

    @QtCore.pyqtProperty(QtCore.QVariant, constant=True)
    def instanceProxy(self):
        return self._instance_proxy

    @QtCore.pyqtProperty(QtCore.QVariant, constant=True)
    def pluginProxy(self):
        return self._plugin_proxy

    @QtCore.pyqtProperty(QtCore.QVariant, constant=True)
    def terminalModel(self):
        return self._terminal_model

    @QtCore.pyqtProperty(QtCore.QVariant, constant=True)
    def terminalProxy(self):
        return self._terminal_proxy

    @QtCore.pyqtSlot(int)
    def toggleItem(self, index):
        self.__toggle_item(self._item_model, index)

    @QtCore.pyqtSlot(int)
    def toggleInstance(self, index):
        qindex = self._instance_proxy.index(index, 0, QtCore.QModelIndex())
        source_qindex = self._instance_proxy.mapToSource(qindex)
        source_index = source_qindex.row()
        self.__toggle_item(self._item_model, source_index)

    @QtCore.pyqtSlot(int, result=QtCore.QVariant)
    def pluginData(self, index):
        qindex = self._plugin_proxy.index(index, 0, QtCore.QModelIndex())
        source_qindex = self._plugin_proxy.mapToSource(qindex)
        source_index = source_qindex.row()
        return self.__item_data(self._item_model, source_index)

    @QtCore.pyqtSlot(int, result=QtCore.QVariant)
    def instanceData(self, index):
        qindex = self._instance_proxy.index(index, 0, QtCore.QModelIndex())
        source_qindex = self._instance_proxy.mapToSource(qindex)
        source_index = source_qindex.row()
        return self.__item_data(self._item_model, source_index)

    @QtCore.pyqtSlot(int)
    def togglePlugin(self, index):
        qindex = self._plugin_proxy.index(index, 0, QtCore.QModelIndex())
        source_qindex = self._plugin_proxy.mapToSource(qindex)
        source_index = source_qindex.row()

        model = self._item_model
        item = model.itemFromIndex(source_index)

        if item.optional:
            self.__toggle_item(self._item_model, source_index)
        else:
            self.error.emit("Plug-in is mandatory")

    @QtCore.pyqtSlot(str, str, str, str)
    def exclude(self, target, operation, role, value):
        """Exclude a `role` of `value` at `target`

        Arguments:
            target (str): Destination proxy model
            operation (str): "add" or "remove" exclusion
            role (str): Role to exclude
            value (str): Value of `role` to exclude

        """

        target = {"terminal": self._terminal_proxy,
                  "instance": self._instance_proxy,
                  "plugin": self._plugin_proxy}[target]

        if operation == "add":
            target.addExclusion(role, value)

        elif operation == "remove":
            target.removeExclusion(role)

        else:
            raise TypeError("operation must be either `add` or `remove`")

    @QtCore.pyqtSlot()
    def reset(self):
        """Request that host re-discovers plug-ins and re-processes selectors

        A reset completely flushes the state of the GUI and reverts
        back to how it was when it first got launched.

        """

        self._terminal_model.reset()
        self._item_model.reset()
        self._changes.update({
            "context": {},
            "plugins": {}
        })

        util.timer("requesting_data")
        response = request("POST", "/state")

        for attempt in range(2):
            if response.status_code == 200:
                break

            self.error.emit("Failed to post state; retrying..")

            time.sleep(0.2)
            response = request("POST", "/state")

        if response.status_code != 200:
            self.error.emit("Could not post state; "
                            "is the server running @ %s?"
                            "Message: %s" % (REST_PORT, response.text))
            return

        response = request("GET", "/state")

        util.timer_end("requesting_data",
                       "Spent %.2f ms requesting data from host")

        if response.status_code != 200:
            self.error.emit("Could not get state; see Terminal")
            self.echo({
                "type": "message",
                "message": response.json()["message"]
            })
            return

        state = response.json()["state"]

        plugins = state.get("plugins", [])
        context = state.get("context", [])

        for plugin in plugins:
            data = plugin["data"]

            if data.get("order") < 1:
                data["isToggled"] = False

            doc = data.get("doc")
            if doc is not None:
                data["doc"] = util.format_docstring(doc)

            item = models.PluginItem(name=plugin["name"],
                                     data=data)
            self._item_model.addItem(item)

        # Log context information
        context_ = {
            "type": "context",
            "name": "Pyblish",
            "filter": "Pyblish"
        }

        context_.update(context["data"])

        self.echo(context_)

        util.invoke(self.select, callback=self.add_instances)

    def select(self):
        for plugin in self._item_model.plugins:
            if not plugin.data.get("order") < 1:
                continue

            pair = {
                "instance": None,
                "plugin": plugin.name
            }

            self.about_to_process_blocking.emit(pair)

            response = request("PUT", "/state", data=pair)

            if response.status_code == 200:
                result = response.json()["result"]
                self.processed_blocking.emit(result)
            else:
                self.error.emit("Selection failed; see terminal")
                self.echo({
                    "type": "message",
                    "message": ("Server responded with code %s "
                                "during selection with %s: \n%s" % (
                                    response.status_code,
                                    plugin.name,
                                    response.json()))
                })

        self.selected.emit()

        # Selection is done, refresh state
        response = request("GET", "/state")
        assert response.status_code == 200

        state = response.json()["state"]
        context = state.get("context", {})
        instances = context.get("children", [])

        return instances

    def add_instances(self, instances):
        for instance in instances:
            if instance["data"].get("publish") is False:
                instance["data"]["isToggled"] = False

            item = models.InstanceItem(name=instance["name"],
                                       data=instance["data"])
            self._item_model.addItem(item)

        # Determine compatibility
        for plugin in self._item_model.plugins:
            has_compatible = False

            for instance in self._item_model.instances:
                if instance.family in plugin.families:
                    has_compatible = True

            index = self._item_model.itemIndexFromItem(plugin)
            self._item_model.setData(index, "hasCompatible", has_compatible)

    @QtCore.pyqtSlot()
    def save(self):
        if not any([self._changes["context"], self._changes["plugins"]]):
            self.error.emit("Nothing to save")
            return

        serialised_changes = json.dumps(self._changes, indent=4)

        response = request("POST", "/state",
                           data={"changes": serialised_changes})

        if response.status_code == 200:
            # changes = json.dumps(response.json()["changes"], indent=4)
            self.info.emit("Changes saved successfully.")
            self.saved.emit()

        else:
            message = response.json().get("message") or "An error occurred"
            self.info.emit(message)
            self.error.emit("Could not save changes; see Terminal")

    def __item_data(self, model, index):
        """Return item data as dict"""
        item = model.itemFromIndex(index)

        data = {
            "name": item.name,
            "data": item.data,
            "doc": getattr(item, "doc", None)
        }

        return data

    def __toggle_item(self, model, index):
        if self.is_running:
            self.error.emit("Cannot untick while publishing")
        else:
            item = model.itemFromIndex(index)
            model.setData(index, "isToggled", not item.isToggled)

    @QtCore.pyqtProperty(QtCore.QObject)
    def log(self):
        return self._log

    def echo(self, data):
        """Append `data` to terminal model"""
        self._terminal_model.addItem(data)

    def __init__(self, parent=None):
        super(Controller, self).__init__(parent)

        item_model = models.Model()
        terminal_model = models.TerminalModel()

        instance_proxy = models.ProxyModel()
        instance_proxy.setSourceModel(item_model)
        instance_proxy.addInclusion(999, "InstanceItem")

        plugin_proxy = models.ProxyModel()
        plugin_proxy.setSourceModel(item_model)

        plugin_proxy.names = item_model.names
        plugin_proxy.addInclusion(999, "PluginItem")
        plugin_proxy.addExclusion("type", "Selector")
        plugin_proxy.addExclusion("hasCompatible", False)

        terminal_proxy = models.ProxyModel()
        terminal_proxy.setSourceModel(terminal_model)
        terminal_proxy.names = terminal_model.names
        terminal_proxy.setFilterRole(terminal_model.names["filter"])  # msg
        terminal_proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        terminal_proxy.addExclusion("levelname", "DEBUG")

        self.is_running = False

        self._has_errors = False
        self._log = util.Log()
        self._state = dict()
        self._changes = {
            "context": {},
            "plugins": {}
        }

        self._item_model = item_model
        self._terminal_model = terminal_model

        self._instance_proxy = instance_proxy
        self._plugin_proxy = plugin_proxy
        self._terminal_proxy = terminal_proxy

        self.info.connect(self.on_info)
        self.error.connect(self.on_error)
        self.finished.connect(self.on_finished)
        self.processed.connect(self.on_processed)
        self.selected.connect(self.on_selected)
        self.about_to_process.connect(self.on_about_to_process)
        self._item_model.data_changed.connect(self.on_data_changed)

        # Blocking signals called from threads.
        self.processed_blocking.connect(
            self.on_processed, type=QtCore.Qt.BlockingQueuedConnection)
        self.about_to_process_blocking.connect(
            self.on_about_to_process, type=QtCore.Qt.BlockingQueuedConnection)

    # Event handlers

    def on_data_changed(self, item, key, old, new):
        """Handler for changes to data within `model`

        Changes include toggling instances along with any
        arbitrary change to members of items within `model`.

        """

        if key not in ("isToggled",):
            return

        remap = {
            "isToggled": "publish"
        }

        key = remap.get(key) or key

        if isinstance(item, models.PluginItem):
            changes = self._changes["plugins"]
        else:
            changes = self._changes["context"]

        name = item.name
        if name not in changes:
            changes[name] = {}

        if key in changes[name]:

            # If the new value equals the old one,
            # we can assume that there was no change.
            if changes[name][key]["old"] == new:
                changes[name].pop(key)

                # It's possible that this discarded change
                # was the only change made to this item.
                # If so, discard the item entirely.
                if not changes[name]:
                    changes.pop(name)

            else:
                changes[name][key]["new"] = new
        else:
            changes[name][key] = {"new": new, "old": old}

    def on_selected(self):
        self.reset_status()

    def on_about_to_process(self, pair):
        """A pair is about to be processed"""
        self.update_models_with_result(pair)

    def on_processed(self, result):
        """A pair has just been processed"""
        self.update_models_with_result(result)

        if getattr(self, "_last_plugin", None) != result["plugin"]:
            self._last_plugin = result["plugin"]

            plugin_name = result["plugin"]
            plugin_item = self._item_model.itemFromName(plugin_name)

            self.echo({
                "type": "plugin",
                "message": result["plugin"],
                "filter": result["plugin"],
                "doc": plugin_item.doc
            })

        self.echo({
            "type": "instance",
            "message": result["instance"],
            "filter": result["instance"]
        })

        for record in result["records"]:
            record["type"] = "record"
            record["filter"] = record["msg"]
            record["msg"] = util.format_docstring(record["msg"])
            self.echo(record)

        if result["error"] is not None:
            error = result["error"]
            error["type"] = "error"
            error["filter"] = error["message"]
            self.echo(error)

    def on_finished(self):
        """Processing has finished"""
        if hasattr(self, "_last_plugin"):
            delattr(self, "_last_plugin")
        self.reset_status()
        self.echo({
            "type": "message",
            "message": "Finished"
        })

    def on_error(self, message):
        """An error has occurred"""
        util.echo(message)

    def on_info(self, message):
        """A message was sent"""
        util.echo(message)

        self.echo({
            "type": "message",
            "message": message
        })

    # Data wranglers

    @QtCore.pyqtSlot()
    def start(self, order=None):
        """Start processing-loop"""

        plugin_toggled = False
        instance_toggled = False

        for item in self._item_model.items:
            if item.isToggled:
                if isinstance(item, models.PluginItem):
                    plugin_toggled = True

                if isinstance(item, models.InstanceItem):
                    instance_toggled = True

        if not any([plugin_toggled, instance_toggled]):
            self.error.emit("Must select at least one instance")
            return

        self.save()
        self.reset_state()
        self.is_running = True

        thread = threading.Thread(target=processor,
                                  args=[self],
                                  name="processor")
        thread.daemon = True
        thread.start()

    @QtCore.pyqtSlot()
    def stop(self, message=None):
        if message:
            self.info.emit(message)
        self.is_running = False

    def update_models_with_result(self, result):
        """Update item-model with result from host

        State is sent from host after processing had taken place
        and represents the events that took place; including
        log messages and completion status.

        """

        model = self._item_model

        for index in range(model.rowCount()):
            model.setData(index, "isProcessing", False)

        if result.get("error") is not None:
            self._has_errors = True

        for type in ("instance", "plugin"):
            name = result[type]
            item = model.itemFromName(name)

            if not item:
                assert type == "instance"
                # No instance were processed.
                continue

            index = model.itemIndexFromItem(item)

            model.setData(index, "isProcessing", True)
            model.setData(index, "currentProgress", 1)

            if result.get("error"):
                model.setData(index, "hasError", True)
            else:
                model.setData(index, "succeeded", True)

        # Logic
        # Do not continue if there are errors
        # and next plug-in is an extractor.

        plugin_name = result["plugin"]
        instance_name = result["instance"]

        plugin_item = [p for p in model.plugins if p.name == plugin_name][0]
        plugin_index = model.plugins.index(plugin_item)

        families = plugin_item.data["families"]

        try:
            instance_item = [i for i in model.instances if i.name == instance_name][0]
            instance_index = model.instances.index(instance_item)
            next_instance = model.instances[instance_index + 1]

            while next_instance.data.get("family") not in families:
                instance_index += 1
                next_instance = model.instances[instance_index]

        except IndexError:
            try:
                next_plugin = model.plugins[plugin_index + 1]
            except IndexError:
                return
            else:
                if self._has_errors and next_plugin.data["order"] >= 2:
                    self.stop("Stopped due to failed vaildation")

    def reset_status(self):
        """Reset progress bars"""
        self._has_errors = False
        self.is_running = False

        for item in self._item_model.items:
            index = self._item_model.itemIndexFromItem(item)
            self._item_model.setData(index, "isProcessing", False)
            self._item_model.setData(index, "currentProgress", 0)

    def reset_state(self):
        """Reset data from last publish"""
        for item in self._item_model.items:
            index = self._item_model.itemIndexFromItem(item)
            self._item_model.setData(index, "hasError", False)
            self._item_model.setData(index, "succeeded", False)


def processor(controller):
    """Publishing processor; executing in a separate thread

    Arguments:
        controller (Controller): Instance of controller to be used
            for processing.
        order (tuple): Range of orders to process. E.g. (0, 1) == between
            0 and 1, including 0 but not 1.

    Logic:
        - Do not process plug-ins without compatible instance
        - Run all validator
        - If any validator fails, do not continue with extractors

    """

    model = controller._item_model

    # Process Context
    #   __
    #  |  |
    #  |  |
    #  |  |
    #  |__|
    #
    for plugin in controller._item_model.plugins:

        # Does the item exist in the proxy?
        proxy = controller._plugin_proxy
        source_row = model.items.index(plugin)
        source_index = model.index(source_row, 0, QtCore.QModelIndex())
        if proxy.mapFromSource(source_index).row() == -1:
            continue

        # Updated by `on_processed`
        if not controller.is_running:
            break

        if plugin.isToggled is False:
            continue

        if plugin.canProcessContext:
            pair = {
                "plugin": plugin.name
            }

            response = request("PUT", "/state", data=pair)
            if response.status_code == 200:
                result = response.json()["result"]
                controller.processed_blocking.emit(result)
            else:
                print json.dumps(response.json(), indent=4)

        if not plugin.canProcessInstance:
            continue

        # Process Instance
        #
        #   /\
        #  /  \
        #  \  /
        #   \/
        #
        for instance in controller._item_model.instances:

            # Updated by `on_processed`
            if not controller.is_running:
                break

            if instance.isToggled is False:
                continue

            family = instance.data["family"]
            if not any(x in plugin.data["families"] for x in (family, "*")):
                continue

            pair = {
                "instance": instance.name,
                "plugin": plugin.name
            }

            controller.about_to_process_blocking.emit(pair)

            response = request("PUT", "/state", data=pair)

            if response.status_code == 200:
                result = response.json()["result"]
                controller.processed_blocking.emit(result)
            else:
                print json.dumps(response.json(), indent=4)

    controller.finished.emit()


def main(port, pid=None, preload=False, debug=False, validate=True):
    """Start the Qt-runtime and show the window

    Arguments:
        port (int): Port through which to communicate
        pid (int, optional): Process id of parent process. Defaults to
            None, thus not being parented to a process and must thus
            be killed manually.
        debug (bool, optional): Whether or not to run in debug-mode.
            Defaults to False
        validate (bool, optional): Whether the environment should be validated
            prior to launching. Defaults to True

    """

    if validate and compat.validate() is False:
        util.echo("""
Could not start application due to a misconfigured environment.

Pass validate=False to pyblish_qml.app:main
in order to bypass validation.
""")

        return 255

    global REST_PORT
    REST_PORT = port

    # Initialise logger for Endpoint
    formatter = logging.Formatter(
        '%(levelname)s - '
        '%(name)s: '
        '%(message)s',
        '%H:%M:%S')
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    for logger in ("endpoint", "werkzeug"):
        log = logging.getLogger(logger)
        log.handlers[:] = []
        log.addHandler(stream_handler)
        log.setLevel(logging.DEBUG)
        # log.setLevel(logging.INFO)

    if debug:
        import mocking
        import threading
        import pyblish_endpoint.server

        os.environ["ENDPOINT_PORT"] = str(port)

        Service = mocking.MockService
        Service.SLEEP_DURATION = 0.1
        # Service.PERFORMANCE = Service.FAST

        endpoint = threading.Thread(
            target=pyblish_endpoint.server.start_production_server,
            kwargs={"port": port, "service": Service})

        endpoint.daemon = True
        endpoint.start()

        util.echo("Running debug app on port: %s" % REST_PORT)

    with util.Timer("Spent %.2f ms creating the application"):
        app = Application()

        app.keep_alive = not debug
        app.listen()

        if not preload:
            app.show()

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
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--validate", action="store_true")

    kwargs = parser.parse_args()
    port = kwargs.port
    pid = kwargs.pid
    preload = kwargs.preload
    debug = kwargs.debug
    validate = kwargs.validate

    return main(port=port,
                pid=pid,
                debug=debug or port == 6000,
                preload=preload,
                validate=validate)


if __name__ == "__main__":
    main(port=6000,
         pid=os.getpid(),
         preload=False,
         debug=True,
         validate=False)
