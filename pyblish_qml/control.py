
import time

# Dependencies
from PyQt5 import QtCore

# Local libraries
import util
import rest
import models


def pyqtConstantProperty(fget):
    return QtCore.pyqtProperty(QtCore.QVariant,
                               fget=fget,
                               constant=True)


class Controller(QtCore.QObject):
    """Handle events coming from QML

    Attributes:
        error (str): [Signal] Outgoing error
        info (str): [Signal] Outgoing message
        processed (dict): [Signal] Finished results from processing
        finished: [Signal] Upon finished publish

    """

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

    def __init__(self, port, parent=None):
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
        self.host = rest.Host(port=port)
        self._state = None
        self._states = list()

        self.info.connect(self.on_info)
        self.error.connect(self.on_error)
        self.finished.connect(self.on_finished)
        # self.item_model.data_changed.connect(self.on_data_changed)

        self.state_changed.connect(self.on_state_changed)

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
        # |_______________|
        # | ____     ____ |
        # ||    |---|    ||
        # ||____|---|____||
        # |_______________|
        #

        hidden.addTransition(self.show, visible)
        visible.addTransition(self.hide, hidden)

        ready.addTransition(self.publishing, publishing)
        ready.addTransition(self.initialising, initialising)
        ready.addTransition(self.repairing, repairing)
        ready.addTransition(self.saving, saving)
        saving.addTransition(self.saved, ready)
        publishing.addTransition(self.stopping, stopping)
        publishing.addTransition(self.finished, finished)
        finished.addTransition(self.initialising, initialising)
        initialising.addTransition(self.initialised, ready)
        stopping.addTransition(self.finished, finished)

        dirty.addTransition(self.initialising, clean)
        clean.addTransition(self.changed, dirty)

        # Set initial states
        for compound, state in {machine: group,
                                visibility: hidden,
                                operation: ready,
                                errored: clean}.items():
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
                      clean):
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

    @QtCore.pyqtSlot(int)
    def toggleInstance(self, index):
        qindex = self.instance_proxy.index(index, 0, QtCore.QModelIndex())
        source_qindex = self.instance_proxy.mapToSource(qindex)
        source_index = source_qindex.row()

        self.__toggle_item(self.item_model, source_index)
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

        model = self.item_model
        item = model.items[source_index]

        if item.optional:
            self.__toggle_item(self.item_model, source_index)
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

        util.async(self.host.save,
                   args=[self.changes],
                   callback=self.saved.emit)

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
        self.result_model.add_item(**data)

    # Event handlers

    def on_state_changed(self, state):
        print "Entering state: \"%s\"" % state

        if state == "ready":
            self.ready.emit()

        self._state = state
        self._states = list(s.name for s in self.machine.configuration())

    def on_data_changed(self, item, key, old, new):
        """Handler for changes to data within `model`

        Changes include toggling instances along with any
        arbitrary change to members of items within `model`.

        """

        if not self.changes:
            self.changed.emit()
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

    # Data wranglers

    def tests(self, type):
        if type == "publish":
            def test(pair):
                if not self.is_running:
                    return False

                plugin, instance = pair

                if plugin.order >= 2:
                    if self.item_model.has_failed_validator():
                        return False

                return True

            return test

        if type == "repair":
            def test(pair):
                if not self.is_running:
                    return False

                return True

            return test

        return lambda pair: True

    def process_next(self, result=None, iterator=None,
                     test=None, on_finished=None):
        """Process next pair

        Compute next pair using `iterator` and pass along
        results to host.

        See :meth:`_next` for more details.

        """

        return self._next(mode="process",
                          result=result,
                          iterator=iterator,
                          test=self.tests("publish"),
                          on_finished=on_finished)

    def repair_next(self, result=None, iterator=None,
                    test=None, on_finished=None):
        """Repair next pair

        Compute next pair using `iterator` and pass along
        results to host.

        See :meth:`_next` for more details.

        """

        return self._next(mode="repair",
                          result=result,
                          test=self.tests("repair"),
                          iterator=iterator,
                          on_finished=on_finished)

    def _next(self,
              mode,
              result=None,
              iterator=None,
              test=None,
              on_finished=None):
        """Process or repair next pair

        Recursive function that computes the next available
        pair of (plugin, instance) and processes it on the host,
        if it passes the test.

        Processing diagram::

             ______         ______
            |      |       |      |
            | draw |------>| next |
            |______|       |______|
               |               |
               |               |
               |               |
               |           ____v___             __________
               |          /        \           |          |
            result        |  test  |---fail--->| finished |
               |          \________/           |__________|
               |               |
               |               |
               |             pass
               |               |
               |           ____v____
               |__________|         |
                          | process |
                          | (async) |
                          |_________|

        IPC calls are made within a loop, the result of each call is
        then returned to the main thread in which they are drawn before
        making another IPC call.

        The reason this complexity is that the drawing must take place
        in the main thread, whereas the processing must occur in a thread,
        so as to not block the GUI.

        Arguments:
            result (dict, Exception, optional): Results from previous
                process, may be either a dictionary of the Result schema,
                or an Exception object depending on how things went.
                If no result is passed, processing starts from the beginning.
            iterator (callable, optional): Alternative generator from which
                to derive (plugin, instance) pairs. Defaults to the one
                provided by :class:`model.ItemModel`.

                A `iterator` evaluate the initial state of a model, whereas
                `test` evaluates the current state of a model. A Test may yield
                different results depending on the current state of a model,
                wheras a Processor yields consistent results regardless of
                any current state.

            test (callable, optional): Alternative test through which a pair
                must pass before processing may continue.

                As opposed to `iterator`, `test` evaluates the current state
                of a model and may yield different results depending on how
                a given process is going.

            on_finished (callable, optional): Called without arguments upon
                reaching the end of processing.

        """

        def finish():
            self.is_running = False
            self.finished.emit()

            if on_finished is not None:
                on_finished()

        if isinstance(result, Exception):
            error = dict()
            error["type"] = "error"
            error["message"] = util.format_text(str(result))
            error["filter"] = error["message"]

            self.echo(error)

            finish()

            return self.error.emit("An error occured, "
                                   "see Terminal for details")

        elif result is not None:
            self.item_model.update_with_result(result)

            # NOTE(marcus): This is temporary
            plugin_name = result["plugin"]
            plugin_item = self.item_model.plugins[plugin_name]
            result["doc"] = plugin_item.doc
            # end

            self.result_model.update_with_result(result)

        if iterator is None:
            iterator = models.ItemIterator(self.item_model)

        if test is None:
            def test(pair):
                return True

        try:
            next = iterator.next()
        except StopIteration:
            next = None

        if next and test(next):
            pair = {"plugin": next[0].name,
                    "instance": getattr(next[1], "name", None)}

            self.item_model.update_current(pair)

            funcs = {
                "process": self.host.process,
                "repair": self.host.repair
            }

            util.async(funcs[mode],
                       args=[pair],
                       callback=lambda result: self._next(
                           mode=mode,
                           result=result,
                           iterator=iterator,
                           test=test,
                           on_finished=on_finished
                       ))

        else:
            finish()

    # Slots

    @QtCore.pyqtSlot()
    def publish(self):
        print "Publishing.."
        if "ready" not in self.states:
            self.error.emit("Not ready")
            return

        self.publishing.emit()
        self.is_running = True
        self.save()
        self.process_next(
            iterator=models.ItemIterator(self.item_model),
            test=self.tests("publish"))

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

        self.initialising.emit()
        self.item_model.reset()
        self.result_model.reset()
        self.changes.clear()

        def init():
            init = self.host.init()
            if isinstance(init, Exception):
                return init

            state = self.host.state()

            return state

        def on_finished(state):
            if isinstance(state, Exception):
                return self.error.emit(str(state))

            self.item_model.update_with_state(state)
            self.result_model.update_with_state(state)

            def selectors():
                for item in self.item_model.plugins:
                    if item.order < 1:
                        yield item, None

            def on_finished():
                state = self.host.state()

                self.item_model.update_with_state(state)
                self.item_model.update_compatibility()

                self.initialised.emit()

                util.timer_end("resetting..",
                               "Spent %.2f ms resetting..")

            self.is_running = True
            self.process_next(iterator=selectors(), on_finished=on_finished)

        util.async(init, callback=on_finished)

    @QtCore.pyqtSlot(int)
    def repairPlugin(self, index):
        if "finished" not in self.states:
            return self.error.emit("Not ready")

        index = self.plugin_proxy.index(index, 0, QtCore.QModelIndex())
        index = self.plugin_proxy.mapToSource(index)

        def iterator(plugin):
            if plugin.canRepairContext:
                yield plugin, None

            for instance in self.item_model.instances:
                if not instance.hasError:
                    continue

                if instance.name not in plugin.compatibleInstances:
                    continue

                yield plugin, instance

        self.publishing.emit()
        self.is_running = True

        plugin = self.item_model.items[index.row()]
        plugin.hasError = False

        self.repair_next(iterator=iterator(plugin))
