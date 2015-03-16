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
import model
import compat
import safety

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

        _changes (dict): Changes made by GUI

    """

    error = QtCore.pyqtSignal(str, arguments=["message"])
    info = QtCore.pyqtSignal(str, arguments=["message"])
    processed = QtCore.pyqtSignal(QtCore.QVariant, arguments=["data"])
    finished = QtCore.pyqtSignal()

    called = QtCore.pyqtSignal(QtCore.QVariant, arguments=["result"])

    @QtCore.pyqtProperty(QtCore.QVariant, constant=True)
    def pluginModel(self):
        return self._plugin_model

    @QtCore.pyqtProperty(QtCore.QVariant, constant=True)
    def instanceModel(self):
        return self._instance_model

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

        if item.data.get("optional"):
            self.__toggle_item(self._plugin_model, index)
        else:
            self.error.emit("Plug-in is mandatory")

    @QtCore.pyqtSlot()
    def reset(self):
        """Request that host re-discovers plug-ins and re-processes selectors

        A reset completely flushes the state of the GUI and reverts
        back to how it was when it first got launched.

        """

        self._changes.clear()

        util.timer("requesting_data")
        response = request("POST", "/state")

        for attempt in range(2):
            if response.status_code == 200:
                break

            self.error.emit("Failed to fetch state; retrying..")

            time.sleep(0.2)
            response = request("POST", "/state")

        if response.status_code != 200:
            self.error.emit("Could not fetch state; "
                            "is the server running @ %s?"
                            "Message: %s" % (REST_PORT, response.text))
            return

        response = request("GET", "/state").json()

        util.timer_end("requesting_data",
                       "Spent %.2f ms requesting data from host")

        state = response.get("state", {})

        # Remove existing items from model
        self._instance_model.reset()
        self._plugin_model.reset()

        context = state.get("context", {})
        instances = context["children"]
        plugins = state.get("plugins", [])

        for data in instances:
            item = model.Item(**data)
            self._instance_model.addItem(item)

        for data in plugins:
            if data.get("hasCompatible") is True and data.get("order") >= 1:
                item = model.Item(**data)
                self._plugin_model.addItem(item)

            else:
                self._changes["plugins"] = [{
                    "name": data["name"],
                    "data": {
                        "publish": False
                    }
                }]

    @QtCore.pyqtSlot()
    def stop(self):
        self.is_running = False

    def __item_data(self, model, index):
        """Return item data as dict"""
        item = model.itemFromIndex(index)
        return item.data

    def __toggle_item(self, model, index):
        if self.is_running:
            self.error.emit("Cannot untick while publishing")
        else:
            item = model.itemFromIndex(index)
            model.setData(index, "publish", not item.data.get("publish"))

    @QtCore.pyqtSlot()
    def publish(self):
        """Perform publish

        This is done in stages.

        1. Collect changes
        2. Update host with changes
        3. Advance until finished

        """

        if self._changes:
            serialised_changes = json.dumps(self._changes, indent=4)
            response = request("POST", "/state",
                               data={"state": serialised_changes})
            if response.status_code != 200:
                self.error.emit(
                    response.json().get("message") or "An error occurred")

                return
        else:
            util.echo("No changes were made")

        self.is_running = True
        self.__start()

    @QtCore.pyqtProperty(QtCore.QObject)
    def log(self):
        return self._log

    def __init__(self, parent=None):
        super(Controller, self).__init__(parent)

        self.is_running = False

        self._has_errors = False
        self._log = util.Log()
        self._state = dict()
        self._changes = dict()

        self._instance_model = model.InstanceModel()
        self._plugin_model = model.PluginModel()

        self.info.connect(self.on_info)
        self.error.connect(self.on_error)
        self.finished.connect(self.on_finished, type=QtCore.Qt.BlockingQueuedConnection)
        self.processed.connect(self.on_processed, type=QtCore.Qt.BlockingQueuedConnection)

        self._instance_model.data_changed.connect(self.on_instance_data_changed)
        self._plugin_model.data_changed.connect(self.on_plugin_data_changed)

    def parse_advance_state(self, state):
        """Parse state produced by advancing

        Given a dictionary of current and future items as indexes,
        return a dictionary with their actual names

        """

        state["plugin"] = state["current_plugin"]
        state["instance"] = state["current_instance"]

    def on_instance_data_changed(self, *args, **kwargs):
        self.on_data_changed(self._instance_model, *args, **kwargs)

    def on_plugin_data_changed(self, *args):
        self.on_data_changed(self._plugin_model, *args)

    def on_data_changed(self, model_, index, role, old, new):
        """Handler for changes to data within `model`

        Changes include toggling instances along with any
        arbitrary change to members of items within `model`.

        Example dictionary of changes:
            {
                "context": {
                    "children": [
                        {
                            "name": "Peter01",
                            "publish": false,
                            "data": {
                                "destination": "/server/published/assets",
                            },
                        }
                    ]
                },
                "plugins": [
                    {
                        "name": "ExtractAsMa",
                        "publish": False
                    }
                ]
            }

        """

        if role not in model.Item.defaults:
            return

        if isinstance(model_, model.PluginModel):
            if "plugins" not in self._changes:
                self._changes["plugins"] = list()
            items = self._changes["plugins"]

        else:
            if "context" not in self._changes:
                self._changes["context"] = {"children": list()}
            items = self._changes["context"]["children"]

        key = role
        value = new

        item = None
        name = model_.itemFromIndex(index).data["name"]
        for i in items:
            if i.get("name") == name:
                item = i
                break

        if item is None:
            item = {"name": name, "data": {key: value}}
            items.append(item)

        else:
            item["data"][key] = value

    def on_processed(self, state):
        """Handler for processed events"""
        self.update_models_with_state(state)

    def on_finished(self):
        """Handler for finished events"""
        self.reset_status()

    def on_error(self, message):
        util.echo(message)

    def on_info(self, message):
        util.echo(message)

    def __start(self):
        """Start processing-loop"""

        if hasattr(self, "__pt") and getattr(self, "__pt").is_alive():
            self.error.emit("Previous processing still active..")
            return

            delattr(self, "__pt")

        def worker():
            response = request("PUT", "/state")

            while self.is_running and response.status_code == 200:
                state = response.json().get("state", {})
                self.parse_advance_state(state)
                self.processed.emit(state)
                response = request("PUT", "/state")

            self.finished.emit()

        self.reset_state()

        thread = threading.Thread(target=worker, name="publisher")
        thread.daemon = True
        thread.start()

        setattr(self, "__pt", thread)

    def update_models_with_state(self, state):
        """Update item-model with state of host

        State is sent from host after processing had taken place
        and represents the events that took place; including
        log messages and completion status.

        """

        name = state["current_instance"]
        if name is not None:
            model_ = self._instance_model
            for item in model_.items:
                index = model_.itemIndex(item)

                if name == item.data["name"]:
                    model_.setData(index, "isProcessing", True)
                    model_.setData(index, "currentProgress", 1)

                    if state.get("error"):
                        model_.setData(index, "hasError", True)
                    else:
                        model_.setData(index, "succeeded", True)

                else:
                    model_.setData(index, "isProcessing", False)
        else:
            print "Updating model, but instance was None: %s" % state

        name = state["current_plugin"]
        if name is not None:
            model_ = self._plugin_model
            for item in model_.items:
                index = model_.itemIndex(item)

                if name == item.data["name"]:
                    if self._has_errors:
                        if item.data["type"] == "Extractor":
                            self.info.emit("Stopped due to failed vaildation")
                            self.is_running = False
                            return

                    model_.setData(index, "isProcessing", True)
                    model_.setData(index, "currentProgress", 1)

                    if state.get("error"):
                        model_.setData(index, "hasError", True)
                        self._has_errors = True
                    else:
                        model_.setData(index, "succeeded", True)

                else:
                    model_.setData(index, "isProcessing", False)
        else:
            print "Updating model, but plugin was None: %s" % state

    def reset_status(self):
        """Reset progress bars"""
        self._has_errors = False
        self.is_running = False

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

    try:
        safety.validate()
    except Exception as e:
        util.echo(
            """Could not start application due to a misconfigured environment.

Pass validate=False to pyblish_qml.app:main
in order to bypass validation.

See below message for more information.
""")

        util.echo("Environment:")
        util.echo("-" * 32)

        for key, value in safety.stats.iteritems():
            util.echo("%s = %s" % (key, value))

        util.echo()
        util.echo("Error:")
        util.echo("-" * 32)
        util.echo(e)
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

    for logger in ("endpoint",):
        log = logging.getLogger(logger)
        log.handlers[:] = []
        log.addHandler(stream_handler)
        # log.setLevel(logging.DEBUG)

    if debug:
        import mocking
        import threading
        import pyblish_endpoint.server

        Service = mocking.MockService
        Service.SLEEP_DURATION = 0.1
        Service.PERFORMANCE = Service.FAST

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

    kwargs = parser.parse_args()
    port = kwargs.port
    pid = kwargs.pid
    preload = kwargs.preload
    debug = kwargs.debug

    return main(port=port,
                pid=pid,
                debug=debug,
                preload=preload)


if __name__ == "__main__":
    main(port=6000,
         pid=os.getpid(),
         preload=False,
         debug=True)
