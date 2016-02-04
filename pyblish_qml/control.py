
import json
import time
import collections

# Dependencies
from PyQt5 import QtCore
import pyblish_rpc.client
import pyblish_rpc.schema
import pyblish.logic
import pyblish.api

# Local libraries
import util
import models

from pyblish_qml import settings


def toggle_instance(instance, new_value, old_value):
    instance.data['publish'] = bool(new_value)

pyblish.api.register_callback("instanceToggled", toggle_instance)


def pyqtConstantProperty(fget):
    return QtCore.pyqtProperty(QtCore.QVariant,
                               fget=fget,
                               constant=True)


class Controller(QtCore.QObject):
    """Communicate with QML"""

    # PyQt Signals
    info = QtCore.pyqtSignal(str, arguments=["message"])
    error = QtCore.pyqtSignal(str, arguments=["message"])

    show = QtCore.pyqtSignal()
    hide = QtCore.pyqtSignal()

    publishing = QtCore.pyqtSignal()
    repairing = QtCore.pyqtSignal()
    stopping = QtCore.pyqtSignal()
    saving = QtCore.pyqtSignal()
    initialising = QtCore.pyqtSignal()
    acting = QtCore.pyqtSignal()
    acted = QtCore.pyqtSignal()

    # A plug-in/instance pair is about to be processed
    about_to_process = QtCore.pyqtSignal(object, object)

    changed = QtCore.pyqtSignal()

    ready = QtCore.pyqtSignal()
    saved = QtCore.pyqtSignal()
    finished = QtCore.pyqtSignal()
    initialised = QtCore.pyqtSignal()

    state_changed = QtCore.pyqtSignal(str, arguments=["state"])

    # PyQt Properties
    itemModel = pyqtConstantProperty(lambda self: self.item_model)
    itemProxy = pyqtConstantProperty(lambda self: self.item_proxy)
    recordProxy = pyqtConstantProperty(lambda self: self.record_proxy)
    errorProxy = pyqtConstantProperty(lambda self: self.error_proxy)
    instanceProxy = pyqtConstantProperty(lambda self: self.instance_proxy)
    pluginProxy = pyqtConstantProperty(lambda self: self.plugin_proxy)
    resultModel = pyqtConstantProperty(lambda self: self.result_model)
    resultProxy = pyqtConstantProperty(lambda self: self.result_proxy)

    def __init__(self, parent=None):
        super(Controller, self).__init__(parent)

        self._temp = [1, 2, 3, 4]

        self.item_model = models.ItemModel()
        self.result_model = models.ResultModel()

        self.instance_proxy = models.InstanceProxy(self.item_model)
        self.plugin_proxy = models.PluginProxy(self.item_model)
        self.result_proxy = models.ResultProxy(self.result_model)

        # Used in Perspective
        self.item_proxy = models.ProxyModel(self.item_model)
        self.record_proxy = models.RecordProxy(self.result_model)
        self.error_proxy = models.ErrorProxy(self.result_model)

        self.changes = dict()
        self.is_running = False
        self.machine = self.setup_statemachine()
        self._state = None
        self._states = list()

        self.info.connect(self.on_info)
        self.error.connect(self.on_error)
        self.finished.connect(self.on_finished)

        # NOTE: Listeners to this signal are run in the main thread
        self.about_to_process.connect(self.on_about_to_process,
                                      QtCore.Qt.QueuedConnection)

        self.state_changed.connect(self.on_state_changed)

        settings.register_port_changed_callback(self.on_client_changed)

        # Connection to host
        self.host = None

    def on_client_changed(self, port):
        """Establish a connection with client

        A client registers interest to QML. Once registered,
        the target host is altered dynamically.

        """

        self.host = pyblish_rpc.client.Proxy(port=port)

    def setup_statemachine(self):
        """Setup and start state machine"""

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
        # |_______________| - Parallell State

        # States that block the underlying GUI
        suspended = util.QState("suspended", group)

        alive = util.QState("alive", suspended)
        acting = util.QState("acting", suspended)
        acted = QtCore.QHistoryState(operation)
        acted.setDefaultState(ready)

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

        hidden.addTransition(self.show, visible)
        visible.addTransition(self.hide, hidden)

        ready.addTransition(self.acting, acting)
        ready.addTransition(self.publishing, publishing)
        ready.addTransition(self.initialising, initialising)
        ready.addTransition(self.repairing, repairing)
        ready.addTransition(self.saving, saving)
        saving.addTransition(self.saved, ready)
        publishing.addTransition(self.stopping, stopping)
        publishing.addTransition(self.finished, finished)
        finished.addTransition(self.initialising, initialising)
        finished.addTransition(self.acting, acting)
        initialising.addTransition(self.initialised, ready)
        stopping.addTransition(self.acted, acted)
        stopping.addTransition(self.finished, finished)

        dirty.addTransition(self.initialising, clean)
        clean.addTransition(self.changed, dirty)

        alive.addTransition(self.acting, acting)
        acting.addTransition(self.acted, acted)

        # Set initial states
        for compound, state in {machine: group,
                                visibility: hidden,
                                operation: ready,
                                errored: clean,
                                suspended: alive}.items():
            compound.setInitialState(state)

        # Make connections
        for state in (hidden,
                      visible,
                      ready,
                      publishing,
                      finished,
                      repairing,
                      initialising,
                      stopping,
                      saving,
                      stopped,
                      dirty,
                      clean,
                      acting,
                      alive,
                      acted):
            state.entered.connect(
                lambda state=state: self.state_changed.emit(state.name))

        machine.start()
        return machine

    @QtCore.pyqtProperty(str, notify=state_changed)
    def state(self):
        return self._state

    @property
    def states(self):
        return self._states

    @QtCore.pyqtSlot(result=float)
    def time(self):
        return time.time()

    def iterator(self, plugins, context):
        """Primary iterator

        CAUTION: THIS RUNS IN A SEPARATE THREAD

        This is the brains of publishing. It handles logic related
        to which plug-in to process with which Instance or Context,
        in addition to stopping when necessary.

        """

        test = pyblish.logic.registered_test()
        state = {
            "nextOrder": None,
            "ordersWithError": set()
        }

        for plug, instance in pyblish.logic.Iterator(plugins, context):
            state["nextOrder"] = plug.order

            if not self.is_running:
                raise StopIteration("Stopped")

            if test(**state):
                raise StopIteration("Stopped due to %s" % test(**state))

            try:
                # Notify GUI before commencing remote processing
                self.about_to_process.emit(plug, instance)

                result = self.host.process(plug, context, instance)

            except Exception as e:
                raise StopIteration("Unknown error: %s" % e)

            else:
                # Make note of the order at which the
                # potential error error occured.
                has_error = result["error"] is not None
                if has_error:
                    state["ordersWithError"].add(plug.order)

            yield result

    @QtCore.pyqtSlot(int, result=QtCore.QVariant)
    def getPluginActions(self, index):
        """Return actions from plug-in at `index`

        Arguments:
            index (int): Index at which item is located in model

        """

        index = self.plugin_proxy.index(index, 0, QtCore.QModelIndex())
        index = self.plugin_proxy.mapToSource(index).row()
        item = self.item_model.items[index]

        # Inject reference to the original index
        actions = [
            dict(action, **{"index": index})
            for action in item.actions
        ]

        # Context specific actions
        for action in list(actions):
            if action["on"] == "failed" and not item.hasError:
                actions.remove(action)
            if action["on"] == "succeeded" and not item.succeeded:
                actions.remove(action)
            if action["on"] == "processed" and not item.processed:
                actions.remove(action)

        # Discard empty groups
        index = 0
        try:
            action = actions[index]
        except IndexError:
            pass
        else:
            while action:
                try:
                    action = actions[index]
                except IndexError:
                    break

                isempty = False

                if action["__type__"] == "category":
                    try:
                        next_ = actions[index + 1]
                        if next_["__type__"] != "action":
                            isempty = True
                    except IndexError:
                        isempty = True

                    if isempty:
                        actions.pop(index)

                index += 1

        return actions

    @QtCore.pyqtSlot(str)
    def runPluginAction(self, action):
        if "acting" in self.states:
            return self.error.emit("Busy")

        elif not any(state in self.states
                     for state in ["ready",
                                   "finished"]):
            return self.error.emit("Busy")

        action = json.loads(action)

        def run():
            util.echo("Running with states.. %s" % self.states)
            self.acting.emit()
            self.is_running = True

            item = self.item_model.items[action["index"]]

            context = self.host.context()
            plugins = self.host.discover()
            plugin = next(x for x in plugins if x.id == item.id)

            result = self.host.process(**{
                "context": context,
                "plugin": plugin,
                "instance": None,
                "action": action["id"]
            })

            return result

        def on_finished(result):
            util.echo("Finished, finishing up..")
            self.is_running = False
            self.acted.emit()

            # Allow running action upon action, without resetting
            self.result_model.update_with_result(result)
            self.info.emit("Success" if result["success"] else "Failed")
            util.echo("Finished with states.. %s" % self.states)

        util.async(run, callback=on_finished)

    @QtCore.pyqtSlot(int)
    def toggleInstance(self, index):
        qindex = self.instance_proxy.index(index, 0, QtCore.QModelIndex())
        source_qindex = self.instance_proxy.mapToSource(qindex)
        source_index = source_qindex.row()
        item = self.item_model.items[source_index]

        if item.optional:
            self.host.emit("instanceToggled", instance=item.name,
                           new_value=not item.isToggled,
                           old_value=item.isToggled)

            self.__toggle_item(self.item_model, source_index)
            self.item_model.update_compatibility()
        else:
            self.error.emit("Cannot toggle")

    @QtCore.pyqtSlot(bool, str)
    def toggleSection(self, checkState, sectionLabel):
        for item in self.item_model.items:
            if item.itemType == 'instance' and sectionLabel == item.family:
                if item.isToggled != checkState:
                    self.host.emit("instanceToggled", instance=item.name,
                                   new_value=not item.isToggled,
                                   old_value=item.isToggled)

                item.isToggled = checkState

            if item.itemType == 'plugin' and item.optional:
                if item.verb == sectionLabel:
                    if item.isToggled != checkState:
                        self.host.emit("pluginToggled", plugin=item.id,
                                       new_value=not item.isToggled,
                                       old_value=item.isToggled)

                    item.isToggled = checkState

        self.item_model.update_compatibility()

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
        item = self.item_model.items[source_index]

        if item.optional:
            self.host.emit("pluginToggled", plugin=item.id,
                           new_value=not item.isToggled,
                           old_value=item.isToggled)

            self.__toggle_item(self.item_model, source_index)
        else:
            self.error.emit("Cannot toggle")

    @QtCore.pyqtSlot(str, str, str, str)
    def exclude(self, target, operation, role, value):
        """Exclude a `role` of `value` at `target`

        Arguments:
            target (str): Destination proxy model
            operation (str): "add" or "remove" exclusion
            role (str): Role to exclude
            value (str): Value of `role` to exclude

        """

        target = {"result": self.result_proxy,
                  "instance": self.instance_proxy,
                  "plugin": self.plugin_proxy}[target]

        if operation == "add":
            target.add_exclusion(role, value)

        elif operation == "remove":
            target.remove_exclusion(role, value)

        else:
            raise TypeError("operation must be either `add` or `remove`")

    @QtCore.pyqtSlot()
    def save(self):
        if not self.changes:
            return

        self.saving.emit()

        # util.async(self.host.save,
        #            args=[self.changes],
        #            callback=self.saved.emit)

    def __item_data(self, model, index):
        """Return item data as dict"""
        item = model.items[index]

        data = {
            "name": item.name,
            "data": item.data,
            "doc": getattr(item, "doc", None),
            "path": getattr(item, "path", None),
        }

        return data

    def __toggle_item(self, model, index):
        if "ready" not in self.states:
            return self.error.emit("Not ready")

        item = model.items[index]

        item.isToggled = not item.isToggled

    def echo(self, data):
        """Append `data` to result model"""
        self.result_model.add_item(data)

    # Event handlers

    def on_about_to_process(self, plugin, instance):
        """Reflect currently running pair in GUI"""

        if instance is None:
            instance_item = self.item_model.instances[0]
        else:
            instance_item = self.item_model.instances[instance.id]

        plugin_item = self.item_model.plugins[plugin.id]

        instance_item.isProcessing = True
        plugin_item.isProcessing = True

    def on_state_changed(self, state):
        util.echo("Entering state: \"%s\"" % state)

        if state == "ready":
            self.ready.emit()

        self._state = state
        self._states = list(s.name for s in self.machine.configuration())

    def on_finished(self):
        self.item_model.reset_status()

        self.echo({
            "type": "message",
            "message": "Finished"
        })

    def on_error(self, message):
        """An error has occurred"""
        util.echo(message)

    def on_info(self, message):
        """A message was sent"""
        self.echo({
            "type": "message",
            "message": message
        })

    # Slots

    @QtCore.pyqtSlot()
    def stop(self):
        self.is_running = False
        self.stopping.emit()

    @QtCore.pyqtSlot()
    def reset(self):
        """Request that host re-discovers plug-ins and re-processes selectors

        A reset completely flushes the state of the GUI and reverts
        back to how it was when it first got launched.

        """

        if not any(state in self.states for state in ("ready", "finished")):
            return self.error.emit("Not ready")

        self.initialising.emit()

        util.timer("resetting..")
        stats = {"requestCount": self.host.stats()["totalRequestCount"]}

        # Clear models
        self.item_model.reset()
        self.result_model.reset()
        self.changes.clear()

        # Clear host
        self.host.reset()

        def on_finished(plugins, context):
            for instance in context:
                self.item_model.add_instance(instance)

            # Compute compatibility
            for plugin in self.item_model.plugins:
                compatible = pyblish.logic.instances_by_plugin(
                    context, plugin)

                if plugin.contextEnabled:
                    c = type("Context", (object,), {"id": "Context"})
                    compatible.append(c)

                if (plugin.instanceEnabled and len(compatible) == 1 and
                   isinstance(compatible[0], type)):
                    compatible = []

                plugin.compatibleInstances = [i.id for i in compatible]

            for instance in self.item_model.instances:
                compatible = list()
                for family in (instance.families or []) + [instance.family]:
                    compatible.extend(pyblish.logic.plugins_by_families(
                        plugins, instance.families + [instance.family]))

                instance.compatiblePlugins = [i.id for i in compatible]

            self.item_model.update_compatibility()

            # Report statistics
            stats["requestCount"] -= self.host.stats()["totalRequestCount"]
            util.timer_end("resetting..", "Spent %.2f ms resetting")
            util.echo("Made %i requests during reset."
                      % abs(stats["requestCount"]))

            # Reset Context
            context = self.item_model.instances[0]
            context.hasError = False
            context.succeeded = False
            context.processed = False
            context.isProcessing = False
            context.currentProgress = 0

            self.initialised.emit()

        def on_run(plugins, context):
            util.async(self.host.context,
                       callback=lambda context: on_finished(plugins, context))

        def on_discover(plugins, context):
            collectors = list()

            for plugin in plugins:
                self.item_model.add_plugin(plugin)

                # Sort out which of these are Collectors
                if not pyblish.lib.inrange(
                        number=plugin.order,
                        base=pyblish.api.Collector.order):
                    continue

                collectors.append(plugin)

            self.run(collectors, [],
                     callback=on_run,
                     callback_args=[plugins, context])

        def on_context(context):
            self.item_model.add_context(context)
            self.result_model.add_context(context)
            util.async(
                self.host.discover,
                callback=lambda plugins: on_discover(plugins, context)
            )

        util.async(self.host.context, callback=on_context)

    @QtCore.pyqtSlot()
    def publish(self):
        """Start asynchonous publishing

        Publishing takes into account all available and currently
        toggled plug-ins and instances.

        """

        def get_data():
            # Communicate with host to retrieve current plugins and instances
            # This can potentially take a very long time; it is run
            # asynchonously and initiates processing once complete.
            host_plugins = dict((p.id, p) for p in self.host.cached_discover)
            host_context = dict((i.id, i) for i in self.host.cached_context)

            plugins = list()
            instances = list()

            for plugin in models.ItemIterator(self.item_model.plugins):

                # Exclude Collectors
                if pyblish.lib.inrange(
                        number=plugin.order,
                        base=pyblish.api.Collector.order):
                    continue

                plugins.append(host_plugins[plugin.id])

            for instance in models.ItemIterator(self.item_model.instances):
                instances.append(host_context[instance.id])

            return plugins, instances

        util.async(get_data, callback=lambda args: self.run(*args))

    @QtCore.pyqtSlot()
    def validate(self):
        """Start asynchonous validation

        Validation only takes into account currently available
        and toggled Validators, and leaves all else behind.

        """

        def get_data():
            # Communicate with host to retrieve current plugins and instances
            # This can potentially take a very long time; it is run
            # asynchonously and initiates processing once complete.
            host_plugins = dict((p.id, p) for p in self.host.cached_discover)
            host_context = dict((i.id, i) for i in self.host.cached_context)

            plugins = list()
            instances = list()

            for plugin in models.ItemIterator(self.item_model.plugins):
                # Consider Validators only.
                if not pyblish.lib.inrange(plugin.order,
                                           base=pyblish.api.Validator.order):
                    continue

                plugins.append(host_plugins[plugin.id])

            for instance in models.ItemIterator(self.item_model.instances):
                instances.append(host_context[instance.id])

            return plugins, instances

        util.async(get_data, callback=lambda args: self.run(*args))

    def run(self, plugins, context, callback=None, callback_args=[]):
        """Commence asynchronous tasks

        This method runs through the provided `plugins` in
        an asynchronous manner, interrupted by either
        completion or failure of a plug-in.

        Inbetween processes, the GUI is fed information
        from the task and redraws itself.

        Arguments:
            plugins (list): Plug-ins to process
            context (list): Instances to process
            callback (func, optional): Called on finish
            callback_args (list, optional): Arguments passed to callback

        """

        # if "ready" not in self.states:
        #     return self.error.emit("Not ready")

        # Initial set-up
        self.is_running = True
        self.publishing.emit()
        self.save()

        # Setup statistics for better debugging.
        # (To be finalised in `on_finished`)
        util.timer("publishing")
        stats = {"requestCount": self.host.stats()["totalRequestCount"]}

        # For each completed task, update
        # the GUI and commence next task.
        def on_next(result):
            if isinstance(result, StopIteration):
                return on_finished(str(result))

            self.item_model.update_with_result(result)
            self.result_model.update_with_result(result)

            # Once the main thread has finished updating
            # the GUI, we can proceed handling of next task.
            util.async(iterator.next, callback=on_next)

        def on_finished(message=None):
            """Locally running function"""
            self.is_running = False
            self.finished.emit()

            if message:
                self.info.emit(message)

            # Report statistics
            stats["requestCount"] -= self.host.stats()["totalRequestCount"]
            util.timer_end("publishing", "Spent %.2f ms resetting")
            util.echo("Made %i requests during publish."
                      % abs(stats["requestCount"]))

            if callback:
                callback(*callback_args)

        # The iterator initiates processing and is
        # executed one item at a time in a separate thread.
        # Once the thread finishes execution, it signals
        # the `callback`.
        iterator = self.iterator(plugins, context)
        util.async(iterator.next, callback=on_next)

    @QtCore.pyqtSlot(int)
    def repairPlugin(self, index):
        if "finished" not in self.states:
            self.error.emit("Not ready")
            return

        self.publishing.emit()
        self.is_running = True
        self.save()

        # Setup statistics
        util.timer("publishing")
        stats = {"requestCount": self.host.stats()["totalRequestCount"]}

        instance_iterator = models.ItemIterator(self.item_model.instances)
        failed_instances = [p.id for p in instance_iterator
                            if p.hasError]

        # Get available items from host
        plugins = collections.OrderedDict(
            (p.id, p) for p in self.host.discover())
        context = collections.OrderedDict(
            (p.id, p) for p in self.host.context()
            if p.id in failed_instances)

        # Filter items in GUI with items from host
        index = self.plugin_proxy.index(index, 0, QtCore.QModelIndex())
        index = self.plugin_proxy.mapToSource(index)
        plugin = self.item_model.items[index.row()]
        plugin.hasError = False

        plugin = plugins[plugin.id]

        iterator = pyblish.logic.process(
            func=self.host.repair,
            plugins=[plugin],
            context=context.values(),
            test=self.host.test)

        def on_next(result):
            if not self.is_running:
                return on_finished()

            if isinstance(result, StopIteration):
                return on_finished()

            if isinstance(result, pyblish.logic.TestFailed):
                self.error.emit(str(result))
                return on_finished()

            if isinstance(result, Exception):
                self.error.emit("Unknown error occured; check terminal")
                self.echo({"type": "message", "message": str(result)})
                return on_finished()

            self.item_model.update_with_result(result)
            self.result_model.update_with_result(result)

            # Run next again
            util.async(iterator.next, callback=on_next)

        def on_finished():
            self.is_running = False
            self.finished.emit()

            # Report statistics
            stats["requestCount"] -= self.host.stats()["totalRequestCount"]
            util.timer_end("publishing", "Spent %.2f ms resetting")
            util.echo("Made %i requests during publish."
                      % abs(stats["requestCount"]))

        # Reset state
        util.async(iterator.next, callback=on_next)
