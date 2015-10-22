
import json
import time
import collections

# Dependencies
from PyQt5 import QtCore
import pyblish_rpc.client
import pyblish_rpc.schema
import pyblish.logic


# Local libraries
import util
import models

from pyblish_qml import settings


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
            print("Running with states.. %s" % self.states)
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
            print("Finished, finishing up..")
            self.is_running = False
            self.acted.emit()

            # Allow running action upon action, without resetting
            self.result_model.update_with_result(result)
            self.info.emit("Success" if result["success"] else "Failed")
            print("Finished with states.. %s" % self.states)

        util.async(run, callback=on_finished)

    @QtCore.pyqtSlot(int)
    def toggleInstance(self, index):
        qindex = self.instance_proxy.index(index, 0, QtCore.QModelIndex())
        source_qindex = self.instance_proxy.mapToSource(qindex)
        source_index = source_qindex.row()
        item = self.item_model.items[source_index]

        if item.optional:
            self.__toggle_item(self.item_model, source_index)
            self.item_model.update_compatibility()
        else:
            self.error.emit("Cannot toggle")

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
            "doc": getattr(item, "doc", None)
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

    def on_state_changed(self, state):
        print "Entering state: \"%s\"" % state

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

        if not any(state in self.states for state in ("ready",
                                                      "finished")):
            return self.error.emit("Not ready")

        util.timer("resetting..")
        stats = {"requestCount": self.host.stats()["totalRequestCount"]}

        self.initialising.emit()
        self.item_model.reset()
        self.result_model.reset()
        self.changes.clear()
        self.host.reset()

        # Append Context
        context = self.host.context()
        self.result_model.add_context(context)

        # Perform selection
        def on_next(result):
            if isinstance(result, StopIteration):
                return on_finished()

            if isinstance(result, Exception):
                self.error.emit("Unknown error occured; check terminal")
                self.echo({"type": "message", "message": str(result)})
                return on_finished("Stopped resetting due to unknown "
                                   "result, check your test?")

            self.result_model.update_with_result(result)
            util.async(iterator.next, callback=on_next)

        def on_finished(message=None):
            for plugin in plugins:
                self.item_model.add_plugin(plugin)

            if message:
                self.echo({"message": message, "type": "message"})

            context = self.host.context()
            self.item_model.add_context(context)

            for instance in context:
                self.item_model.add_instance(instance)

            # Compute compatibility
            for plugin in self.item_model.plugins:
                compatible = pyblish.logic.instances_by_plugin(context, plugin)
                if not plugin.instanceEnabled:
                    compatible += [type("Context",
                                   (object,),
                                   {"id": "Context"})]
                plugin.compatibleInstances = [i.id for i in compatible]

            for instance in self.item_model.instances:
                compatible = pyblish.logic.plugins_by_family(
                    plugins, instance.family)
                instance.compatiblePlugins = [i.id for i in compatible]

            self.item_model.update_compatibility()

            # Report statistics
            stats["requestCount"] -= self.host.stats()["totalRequestCount"]
            util.timer_end("resetting..", "Spent %.2f ms resetting")
            util.echo("Made %i requests during reset."
                      % abs(stats["requestCount"]))

            self.initialised.emit()

        # Append plug-ins
        plugins = self.host.discover()

        iterator = pyblish.logic.process(
                func=self.host.process,
                plugins=[p for p in plugins
                         if pyblish.lib.inrange(
                            number=p.order,
                            base=pyblish.api.Collector.order,
                            offset=0.5)],
                context=self.host.context,
                test=self.host.test)

        util.async(iterator.next, callback=on_next)

    @QtCore.pyqtSlot()
    def publish(self):
        # 1. Get available items from host
        plugins = self.host.discover()
        context = self.host.context()

        # 2. Get toggled items
        _plugins = [x.id for x in models.ItemIterator(
            self.item_model.plugins)]
        _context = [x.id for x in models.ItemIterator(
            self.item_model.instances)]

        # 3. Map toggled items to items from host
        plugins = [x for x in plugins if x.id in _plugins]
        context = [x for x in context if x.id in _context]

        iterator = pyblish.logic.process(func=self.host.process,
                                         plugins=plugins,
                                         context=context,
                                         test=self.host.test)

        return self.run(iterator)

    @QtCore.pyqtSlot()
    def validate(self):
        context = [p.id for p in models.ItemIterator(
            self.item_model.instances)]

        plugins = list()
        for plugin in models.ItemIterator(self.item_model.plugins):
            if not pyblish.lib.inrange(
                    plugin.order, base=pyblish.api.Validator.order):
                continue

            plugins.append(plugin.id)

        plugins = [p for p in self.host.discover() if p.id in plugins]
        context = [p for p in self.host.context() if p.id in context]

        iterator = pyblish.logic.process(func=self.host.process,
                                         plugins=plugins,
                                         context=context,
                                         test=self.host.test)

        return self.run(iterator)

    def run(self, iterator):
        if "ready" not in self.states:
            self.error.emit("Not ready")
            return

        self.publishing.emit()
        self.is_running = True
        self.save()

        # Setup statistics
        util.timer("publishing")
        stats = {"requestCount": self.host.stats()["totalRequestCount"]}

        def on_next(result):
            if isinstance(result, StopIteration):
                return on_finished()

            if not self.is_running:
                return on_finished("Stopped")

            if isinstance(result, pyblish.logic.TestFailed):
                return on_finished("Stopped due to %s" % result)

            if isinstance(result, Exception):
                self.error.emit("Unknown error occured; check terminal")
                self.echo({"type": "message", "message": str(result)})
                return on_finished("Stopped due to unknown error")

            self.update_with_result(result)

            # TODO(marcus): Highlight upcoming pair

            # Run next
            util.async(iterator.next, callback=on_next)

        def on_finished(message=None):
            self.is_running = False
            self.finished.emit()

            if message:
                self.echo({"message": message, "type": "message"})

            # Report statistics
            stats["requestCount"] -= self.host.stats()["totalRequestCount"]
            util.timer_end("publishing", "Spent %.2f ms resetting")
            util.echo("Made %i requests during publish."
                      % abs(stats["requestCount"]))

        # Publish
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

            self.update_with_result(result)

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

    def update_with_result(self, result):
        self.item_model.update_with_result(result)
        self.result_model.update_with_result(result)
