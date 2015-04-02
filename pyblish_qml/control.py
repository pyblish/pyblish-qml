# Standard library
import json

# Dependencies
from PyQt5 import QtCore

# Local libraries
import util
import rest
import models


class Controller(QtCore.QObject):
    """Handle events coming from QML

    Attributes:
        error (str): [Signal] Outgoing error
        info (str): [Signal] Outgoing message
        processing (dict): [Signal] Results before processing begins
        processed (dict): [Signal] Finished results from processing
        finished: [Signal] Upon finished publish

    """

    error = QtCore.pyqtSignal(str, arguments=["message"])
    info = QtCore.pyqtSignal(str, arguments=["message"])

    processing = QtCore.pyqtSignal(QtCore.QVariant, arguments=["pair"])
    processed = QtCore.pyqtSignal(QtCore.QVariant, arguments=["data"])

    finished = QtCore.pyqtSignal()
    saved = QtCore.pyqtSignal()
    selected = QtCore.pyqtSignal()

    s_show = QtCore.pyqtSignal()
    s_hide = QtCore.pyqtSignal()

    s_publishing = QtCore.pyqtSignal()
    s_repairing = QtCore.pyqtSignal()
    s_stopping = QtCore.pyqtSignal()
    s_saving = QtCore.pyqtSignal()
    s_initialising = QtCore.pyqtSignal()

    s_plugin_failure = QtCore.pyqtSignal()

    s_stopped = QtCore.pyqtSignal()
    s_saved = QtCore.pyqtSignal()
    s_failed = QtCore.pyqtSignal()
    s_finished = QtCore.pyqtSignal()
    s_initialised = QtCore.pyqtSignal()

    stateChanged = QtCore.pyqtSignal(str, arguments=["state"])

    # Thread-safe signals
    processing_blocking = QtCore.pyqtSignal(QtCore.QVariant, arguments=["pair"])
    processed_blocking = QtCore.pyqtSignal(QtCore.QVariant, arguments=["data"])

    def __init__(self, port, parent=None):
        super(Controller, self).__init__(parent)

        self.item_model = models.Model()
        self.terminal_model = models.TerminalModel()

        self.instance_proxy = models.InstanceProxy(self.item_model)
        self.plugin_proxy = models.PluginProxy(self.item_model)
        self.terminal_proxy = models.TerminalProxy(self.terminal_model)

        self.port = port
        self.changes = dict()
        self.is_running = False
        self.machine = self.setup_statemachine()

        self.info.connect(self.on_info)
        self.error.connect(self.on_error)
        self.processed.connect(self.on_processed)
        self.selected.connect(self.on_selected)
        self.processing.connect(self.on_processing)
        self.s_finished.connect(self.on_finished)
        self.item_model.data_changed.connect(self.on_data_changed)

        # Blocking handlers signalled from threads.
        bqc = QtCore.Qt.BlockingQueuedConnection
        self.processed_blocking.connect(self.on_processed, type=bqc)
        self.processing_blocking.connect(self.on_processing, type=bqc)

        def qt_message_handler(typ, ctx, msg):
            util.echo("qt: %s" % msg)
            self.echo({
                "type": "message",
                "message": msg
            })

        QtCore.qInstallMessageHandler(qt_message_handler)

        self.stateChanged.connect(self.temp)

    def setup_statemachine(self):
        machine = QtCore.QStateMachine()

        #  _______________
        # |               |
        # |               |
        # |               |
        # |_______________|
        #
        group = util.QState("group", QtCore.QState.ParallelStates, machine)

        #  _______________
        # | ____     ____ |
        # ||    |---|    ||
        # ||____|---|____||
        # |_______________| - Parallell State
        #
        visibility = util.QState("visibility", group)

        hidden = util.QState("hidden", visibility)
        visible = util.QState("visible", visibility)

        #  _______________
        # | ____     ____ |
        # ||    |---|    ||
        # ||____|---|____||
        # |_______________| - Parallell State
        #
        operation = util.QState("operation", group)

        ready = util.QState("ready", operation)
        publishing = util.QState("publishing", operation)
        finished = util.QState("finished", operation)
        repairing = util.QState("repairing", operation)
        initialising = util.QState("initialising", operation)
        stopping = util.QState("stopping", operation)
        stopped = util.QState("stopped", operation)
        saving = util.QState("saving", operation)

        #  _______________
        # | ____     ____ |
        # ||    |---|    ||
        # ||____|---|____||
        # |_______________| - Parallell State
        #
        errored = util.QState("errored", group)

        clean = util.QState("clean", errored)
        dirty = util.QState("dirty", errored)

        #  _______________
        # | ____     ____ |
        # ||    |---|    ||
        # ||____|---|____||
        # |_______________|
        # | ____     ____ |
        # ||    |---|    ||
        # ||____|---|____||
        # |_______________|
        #
        hidden.addTransition(self.s_show, visible)
        visible.addTransition(self.s_hide, hidden)

        ready.addTransition(self.s_publishing, publishing)
        ready.addTransition(self.s_initialising, initialising)
        ready.addTransition(self.s_repairing, repairing)
        ready.addTransition(self.s_saving, saving)
        saving.addTransition(self.s_saved, ready)
        publishing.addTransition(self.s_stopping, stopping)
        publishing.addTransition(self.s_finished, finished)
        finished.addTransition(self.s_initialising, initialising)
        initialising.addTransition(self.s_initialised, ready)
        stopping.addTransition(self.s_stopped, stopped)
        stopped.addTransition(self.s_finished, finished)

        dirty.addTransition(self.s_initialising, clean)
        clean.addTransition(self.s_plugin_failure, dirty)

        # Set initial states
        for compound, state in {machine: group,
                                visibility: hidden,
                                operation: initialising,
                                errored: clean}.items():
            compound.setInitialState(state)

        # Make connections
        hidden.entered.connect(self.hidden_entered)
        visible.entered.connect(self.visible_entered)

        ready.entered.connect(self.ready_entered)
        publishing.entered.connect(self.publishing_entered)
        finished.entered.connect(self.finished_entered)
        repairing.entered.connect(self.repairing_entered)
        initialising.entered.connect(self.initialising_entered)
        stopping.entered.connect(self.stopping_entered)
        saving.entered.connect(self.saving_entered)
        stopped.entered.connect(self.stopped_entered)

        dirty.entered.connect(self.dirty_entered)
        clean.entered.connect(self.clean_entered)

        machine.start()

        return machine

    @QtCore.pyqtProperty(QtCore.QVariant, constant=True)
    def instanceProxy(self):
        return self.instance_proxy

    @QtCore.pyqtProperty(QtCore.QVariant, constant=True)
    def pluginProxy(self):
        return self.plugin_proxy

    @QtCore.pyqtProperty(QtCore.QVariant, constant=True)
    def terminalModel(self):
        return self.terminal_model

    @QtCore.pyqtProperty(QtCore.QVariant, constant=True)
    def terminalProxy(self):
        return self.terminal_proxy

    @QtCore.pyqtSlot(int)
    def toggleInstance(self, index):
        qindex = self.instance_proxy.index(index, 0, QtCore.QModelIndex())
        source_qindex = self.instance_proxy.mapToSource(qindex)
        source_index = source_qindex.row()
        self.__toggle_item(self.item_model, source_index)
        self.update_compatibility()

    @QtCore.pyqtSlot(int, result=QtCore.QVariant)
    def pluginData(self, index):
        qindex = self.plugin_proxy.index(index, 0, QtCore.QModelIndex())
        source_qindex = self.plugin_proxy.mapToSource(qindex)
        source_index = source_qindex.row()
        return self.__item_data(self.item_model, source_index)

    @QtCore.pyqtSlot(int, result=QtCore.QVariant)
    def instanceData(self, index):
        qindex = self.instance_proxy.index(index, 0, QtCore.QModelIndex())
        source_qindex = self.instance_proxy.mapToSource(qindex)
        source_index = source_qindex.row()
        return self.__item_data(self.item_model, source_index)

    @QtCore.pyqtSlot(int)
    def togglePlugin(self, index):
        qindex = self.plugin_proxy.index(index, 0, QtCore.QModelIndex())
        source_qindex = self.plugin_proxy.mapToSource(qindex)
        source_index = source_qindex.row()

        model = self.item_model
        item = model.itemFromIndex(source_index)

        if item.optional:
            self.__toggle_item(self.item_model, source_index)
        else:
            self.error.emit("Plug-in is mandatory")

    @QtCore.pyqtSlot(int)
    def repairInstance(self, index):
        print "Repairing %s" % index

    @QtCore.pyqtSlot(int)
    def repairPlugin(self, index):
        index = self.plugin_proxy.index(index, 0, QtCore.QModelIndex())
        index = self.plugin_proxy.mapToSource(index)
        item = self.item_model.itemFromIndex(index.row())

        self.item_model.setData(index, "hasError", False)

        def _repair(plugin):
            for instance in self.item_model.instances:
                if not instance.hasError:
                    continue

                # NOTE(marcus): We need to find a better way of separating
                # this logic as it is currently being reused all over
                # the place.
                if instance.family not in plugin.families:
                    continue

                result = self.service.repair_context(
                    plugin=plugin.name,
                    on_error=self.error.emit)

                self.processed_blocking.emit(result)

            self.s_finished.emit()

        util.invoke(_repair, args=[item])

    @QtCore.pyqtSlot(str, str, str, str)
    def exclude(self, target, operation, role, value):
        """Exclude a `role` of `value` at `target`

        Arguments:
            target (str): Destination proxy model
            operation (str): "add" or "remove" exclusion
            role (str): Role to exclude
            value (str): Value of `role` to exclude

        """

        target = {"terminal": self.terminal_proxy,
                  "instance": self.instance_proxy,
                  "plugin": self.plugin_proxy}[target]

        if operation == "add":
            target.addExclusion(role, value)

        elif operation == "remove":
            target.removeExclusion(role)

        else:
            raise TypeError("operation must be either `add` or `remove`")

    def update_compatibility(self):
        for plugin in self.item_model.plugins:
            has_compatible = False

            for instance in self.item_model.instances:
                if not instance.isToggled:
                    continue

                if any(x in plugin.families for x in (instance.family, "*")):
                    has_compatible = True
                    break

            index = self.item_model.itemIndexFromItem(plugin)
            self.item_model.setData(index, "hasCompatible", has_compatible)

    @QtCore.pyqtSlot()
    def save(self):
        if not self.changes:
            return

        self.s_saving.emit()

        def save():
            response = self.request("POST", "/state", data={
                "changes": json.dumps(self.changes, indent=4)})

            if response.status_code != 200:
                message = response.json().get("message") or "An error occurred"
                self.error.emit(message)

        util.invoke(save, callback=self.s_saved.emit)

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

    def echo(self, data):
        """Append `data` to terminal model"""
        self.terminal_model.addItem(data)

    def request(self, *args, **kwargs):
        return rest.request("http://127.0.0.1",
                            self.port, *args, **kwargs)

    def temp(self, state):
        print "Entering state: \"%s\"" % state

    # States

    def hidden_entered(self):
        self.stateChanged.emit("hidden")

    def visible_entered(self):
        self.stateChanged.emit("visible")

    def ready_entered(self):
        self.stateChanged.emit("ready")

    def publishing_entered(self):
        self.stateChanged.emit("publishing")

    def finished_entered(self):
        self.stateChanged.emit("finished")

    def repairing_entered(self):
        self.stateChanged.emit("repairing")

    def initialising_entered(self):
        self.stateChanged.emit("initialising")

    def stopping_entered(self):
        self.stateChanged.emit("stopping")

    def stopped_entered(self):
        self.stateChanged.emit("stopped")
        self.s_finished.emit()

    def saving_entered(self):
        self.stateChanged.emit("saving")

    def clean_entered(self):
        self.stateChanged.emit("clean")

    def dirty_entered(self):
        self.stateChanged.emit("dirty")

    # Event handlers

    def on_data_changed(self, item, key, old, new):
        """Handler for changes to data within `model`

        Changes include toggling instances along with any
        arbitrary change to members of items within `model`.

        """

        if not self.changes:
            self.changes = {"plugins": dict(), "context": dict()}

        if key not in ("isToggled",):
            return

        remap = {
            "isToggled": "publish"
        }

        key = remap.get(key) or key

        if isinstance(item, models.PluginItem):
            changes = self.changes["plugins"]
        else:
            changes = self.changes["context"]

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

    def on_finished(self):
        self.reset_status()

        self.echo({
            "type": "message",
            "message": "Finished"
        })

    def on_processing(self, pair):
        """A pair is about to be processed"""
        self.update_models_with_result(pair)

    def on_processed(self, result):
        """A pair has just been processed"""
        self.update_models_with_result(result)
        self.update_terminal_with_result(result)

        for plugin, errors in self.item_model.errors().items():
            if plugin.order >= 1 and plugin.hasError:
                self.s_plugin_failure.emit()

    def on_error(self, message):
        """An error has occurred"""
        util.echo(message)

    def on_info(self, message):
        """A message was sent"""
        self.echo({
            "type": "message",
            "message": message
        })

    # Data wranglers

    def states(self):
        return list(s.name for s in self.machine.configuration())

    # Slots

    @QtCore.pyqtSlot()
    def publish(self):
        if "ready" not in self.states():
            self.error.emit("Not ready")
            return

        self.s_publishing.emit()

        util.invoke(
            self._publish,
            kwargs={"on_processing": self.processing_blocking.emit,
                    "on_processed": self.processed_blocking.emit},
            callback=self.s_finished.emit)

    def _publish(self, on_processing, on_processed):
        """Start publishing-loop"""

        self.is_running = True
        self.save()

        model = self.item_model
        generator = model.pairs()
        for plugin, instance in generator:
            if not self.is_running:
                self.s_stopped.emit()
                break

            if plugin.order >= 2 and model.has_failed_validator():
                self.error.emit("Stopped due to failed validation")
                break

            pair = {"plugin": plugin.name,
                    "instance": getattr(instance, "name", None)}

            on_processing(pair)

            response = self.request("PUT", "/state", data=pair)
            if response.status_code == 200:
                result = response.json()["result"]
            else:
                self.error.emit("There was an error whilst publishing")
                result = response.json()

            on_processed(result)

    @QtCore.pyqtSlot()
    def stop(self):
        self.is_running = False
        self.s_stopping.emit()

    @QtCore.pyqtSlot()
    def reset(self):
        """Request that host re-discovers plug-ins and re-processes selectors

        A reset completely flushes the state of the GUI and reverts
        back to how it was when it first got launched.

        """

        self.s_initialising.emit()

        if not any(state in self.states() for state in ("ready",
                                                        "finished",
                                                        "initialising")):
            self.error.emit("Can't reset from state: %s" % self.states())
            return

        # Clear memory
        self.changes.clear()

        util.timer("Resetting..")

        def init(_):
            response = self.request("POST", "/state")
            if response.status_code != 200:
                self.error.emit(response.json()["message"])

        def get(_):
            response = self.request("GET", "/state")
            if response.status_code != 200:
                self.error.emit(response.json()["message"])
                raise IOError

            return response.json()["state"]

        def select(_):
            for plugin in self.item_model.plugins:
                if not plugin.data["order"] < 1:
                    continue

                response = self.request("PUT", "/state", data={
                    "plugin": plugin.name,
                    "instance": None
                })

                if response.status_code == 200:
                    result = response.json()["result"]
                    self.processed_blocking.emit(result)
                else:
                    self.error.emit(response.json()["message"])

        def draw_plugins(state):
            self.update_model_with_state(state)
            self.update_terminal_with_state(state)
            util.invoke(util.chain,
                        args=(select, get),
                        callback=draw_selection)

        def draw_selection(state):
            self.update_model_with_state(state)
            self.update_compatibility()
            self.s_initialised.emit()
            util.timer_end("Resetting..",
                           "Spent %.4f ms resetting")

        util.invoke(util.chain,
                    args=(init, get),
                    callback=draw_plugins)

    def update_model_with_state(self, state):
        self.item_model.reset()

        plugins = state.get("plugins", list())
        context = state.get("context", dict(children=list()))

        for plugin in plugins:
            data = plugin["data"]

            if data.get("order") < 1:
                data["isToggled"] = False

            doc = data.get("doc")
            if doc is not None:
                data["doc"] = util.format_text(doc)

            item = models.PluginItem(name=plugin["name"],
                                     data=data)
            self.item_model.addItem(item)

        for instance in context["children"]:
            name = instance.get("name")
            data = instance.get("data", {})

            if data.get("publish") is False:
                data["isToggled"] = False

            item = models.InstanceItem(name=name, data=data)
            self.item_model.addItem(item)

    def update_terminal_with_state(self, state):
        self.terminal_model.reset()

        context_ = {
            "type": "context",
            "name": "Pyblish",
            "filter": "Pyblish"
        }

        context_.update(state["context"]["data"])

        self.echo(context_)

    def update_models_with_result(self, result):
        """Update item-model with result from host

        State is sent from host after processing had taken place
        and represents the events that took place; including
        log messages and completion status.

        """

        model = self.item_model

        for index in range(model.rowCount()):
            model.setData(index, "isProcessing", False)

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

                item.errors.append({
                    "source": name,
                    "error": result.get("error")
                })

            else:
                model.setData(index, "succeeded", True)

            if result.get("records"):
                for record in result.get("records"):
                    item.records.append(record)

    def update_terminal_with_result(self, result):
        parsed = self.parse_result_for_terminal(result)

        if getattr(self, "_last_plugin", None) != result["plugin"]:
            self._last_plugin = result["plugin"]
            self.echo(parsed["plugin"])

        self.echo(parsed["instance"])

        for record in result["records"]:
            self.echo(record)

        if parsed["error"] is not None:
            self.echo(parsed["error"])

    def parse_result_for_terminal(self, result):
        plugin_name = result["plugin"]
        plugin_item = self.item_model.itemFromName(plugin_name)

        plugin_msg = {
            "type": "plugin",
            "message": result["plugin"],
            "filter": result["plugin"],
            "doc": plugin_item.doc
        }

        instance_msg = {
            "type": "instance",
            "message": result["instance"],
            "filter": result["instance"],
            "duration": result["duration"]
        }

        record_msgs = list()

        for record in result["records"]:
            record["type"] = "record"
            record["filter"] = record["msg"]
            record["msg"] = util.format_text(record["msg"])
            record_msgs.append(record)

        error_msg = None

        if result["error"] is not None:
            error = result["error"]
            error["type"] = "error"
            error["message"] = util.format_text(error["message"])
            error["filter"] = error["message"]
            error_msg = error

        return {
            "plugin": plugin_msg,
            "instance": instance_msg,
            "records": record_msgs,
            "error": error_msg
        }

    def reset_status(self):
        """Reset progress bars"""
        self.is_running = False

        for item in self.item_model.items:
            index = self.item_model.itemIndexFromItem(item)
            self.item_model.setData(index, "isProcessing", False)
            self.item_model.setData(index, "currentProgress", 0)
