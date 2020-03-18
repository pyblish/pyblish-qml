
import json
import time
import collections

# Dependencies
import pyblish.logic

# Local libraries
from . import util, models, version, settings
from .vendor.Qt5 import QtCore

qtproperty = util.qtConstantProperty


class Controller(QtCore.QObject):
    """Communicate with QML"""

    # Signals
    info = QtCore.Signal(str, arguments=["message"])
    error = QtCore.Signal(str, arguments=["message"])

    show = QtCore.Signal()
    hide = QtCore.Signal()

    firstRun = QtCore.Signal()

    collecting = QtCore.Signal()
    validating = QtCore.Signal()
    extracting = QtCore.Signal()
    integrating = QtCore.Signal()

    repairing = QtCore.Signal()
    stopping = QtCore.Signal()
    saving = QtCore.Signal()
    initialising = QtCore.Signal()
    acting = QtCore.Signal()
    acted = QtCore.Signal()

    # A plug-in/instance pair is about to be processed
    about_to_process = QtCore.Signal(object, object)

    changed = QtCore.Signal()

    ready = QtCore.Signal()
    saved = QtCore.Signal()
    finished = QtCore.Signal()
    initialised = QtCore.Signal()
    commented = QtCore.Signal()
    commenting = QtCore.Signal(str, arguments=["comment"])

    state_changed = QtCore.Signal(str, arguments=["state"])

    # Statically expose these members to the QML run-time.
    itemModel = qtproperty(lambda self: self.data["models"]["item"])
    itemProxy = qtproperty(lambda self: self.data["proxies"]["item"])
    recordProxy = qtproperty(lambda self: self.data["proxies"]["record"])
    errorProxy = qtproperty(lambda self: self.data["proxies"]["error"])
    instanceProxy = qtproperty(lambda self: self.data["proxies"]["instance"])
    pluginProxy = qtproperty(lambda self: self.data["proxies"]["plugin"])
    resultModel = qtproperty(lambda self: self.data["models"]["result"])
    resultProxy = qtproperty(lambda self: self.data["proxies"]["result"])

    def __init__(self, host, parent=None):
        super(Controller, self).__init__(parent)

        # Connection to host
        self.host = host

        self.data = {
            "models": {
                "item": models.ItemModel(),
                "result": models.ResultModel(),
            },
            "comment": "",
            "firstRun": True,
        }

        self.data.update({
            "proxies": {
                "item": models.ProxyModel(self.data["models"]["item"]),

                "instance": models.ProxyModel(
                    self.data["models"]["item"],
                    includes={"itemType": ["instance"]}),

                "plugin": models.ProxyModel(
                    self.data["models"]["item"],
                    includes={"itemType": "plugin"},
                    excludes={"hasCompatible": [False]}),

                # Terminal
                "result": models.ProxyModel(
                    self.data["models"]["result"],
                    excludes={"levelname": ["DEBUG"]}),

                # Perspective
                "record": models.ProxyModel(
                    self.data["models"]["result"],
                    includes={"type": ["record"]}),

                "error": models.ProxyModel(
                    self.data["models"]["result"],
                    includes={"type": ["error"]})
            },
            "state": {
                "is_running": False,
                "readyCount": 0,
                "current": None,
                "all": list(),

                "testPassed": False,
            }
        })

        # Install state machine
        # ---------------------
        # This is what enables complex combinations of state
        # to appear as one, such that one may register interest in
        # e.g. a "finished" state, when "finished" may actually be
        # a combination of multiple child states.
        self.machine = self.setup_statemachine()

        self.info.connect(self.on_info)
        self.error.connect(self.on_error)
        self.finished.connect(self.on_finished)
        self.ready.connect(self.on_ready)
        self.show.connect(self.on_show)

        # NOTE: Listeners to this signal are run in the main thread
        self.about_to_process.connect(self.on_about_to_process,
                                      QtCore.Qt.QueuedConnection)

        self.state_changed.connect(self.on_state_changed)
        self.commenting.connect(self.on_commenting)

    def on_show(self):
        self.host.emit("pyblishQmlShown")

    def dispatch(self, func, *args, **kwargs):
        return getattr(self.host, func)(*args, **kwargs)

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

        collecting = util.QState("collecting", operation)
        validating = util.QState("validating", operation)
        extracting = util.QState("extracting", operation)
        integrating = util.QState("integrating", operation)

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
        ready.addTransition(self.validating, validating)
        ready.addTransition(self.initialising, initialising)
        ready.addTransition(self.repairing, repairing)
        ready.addTransition(self.saving, saving)
        saving.addTransition(self.saved, ready)

        collecting.addTransition(self.initialised, ready)
        collecting.addTransition(self.stopping, stopping)

        validating.addTransition(self.stopping, stopping)
        validating.addTransition(self.finished, finished)
        validating.addTransition(self.extracting, extracting)

        extracting.addTransition(self.stopping, stopping)
        extracting.addTransition(self.finished, finished)
        extracting.addTransition(self.integrating, integrating)

        integrating.addTransition(self.stopping, stopping)
        integrating.addTransition(self.finished, finished)

        finished.addTransition(self.initialising, initialising)
        finished.addTransition(self.acting, acting)
        initialising.addTransition(self.collecting, collecting)
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
                      collecting,
                      validating,
                      extracting,
                      integrating,
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

    @QtCore.Slot(result=str)
    def comment(self):
        """Return first line of comment"""
        return self.data["comment"]

    @QtCore.Property(str, notify=state_changed)
    def state(self):
        return self.data["state"]["current"]

    @QtCore.Property(bool, notify=commented)
    def hasComment(self):
        return True if self.data["comment"] else False

    @QtCore.Property(bool, constant=True)
    def commentEnabled(self):
        return "comment" in self.host.cached_context.data

    @property
    def states(self):
        return self.data["state"]["all"]

    @QtCore.Slot(result=float)
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

        signals = {
            pyblish.api.ValidatorOrder: self.validating,
            pyblish.api.ExtractorOrder: self.extracting,
            pyblish.api.IntegratorOrder: self.integrating,
        }

        for plug, instance in iterator(plugins, context):

            if instance is not None and not instance.data.get("publish", True):
                continue

            state["nextOrder"] = plug.order

            for order in list(signals.keys()):
                if pyblish.lib.inrange(plug.order, order):
                    signals.pop(order).emit()

            if not self.data["state"]["is_running"]:
                return StopIteration("Stopped")

            if test(**state):
                self.data["state"]["testPassed"] = False
                return StopIteration("Stopped due to %s" % test(**state))

            self.data["state"]["testPassed"] = True

            try:
                # Notify GUI before commencing remote processing
                self.about_to_process.emit(plug, instance)

                result = self.host.process(plug, context, instance)

            except Exception as e:
                return StopIteration("Unknown error: %s" % e)

            else:
                # Make note of the order at which the
                # potential error error occured.
                has_error = result["error"] is not None
                if has_error:
                    state["ordersWithError"].add(plug.order)

            yield result

    @QtCore.Slot(int, result="QVariant")
    def getPluginActions(self, index):
        """Return actions from plug-in at `index`

        Arguments:
            index (int): Index at which item is located in model

        """

        index = self.data["proxies"]["plugin"].mapToSource(
            self.data["proxies"]["plugin"].index(
                index, 0, QtCore.QModelIndex())).row()
        item = self.data["models"]["item"].items[index]

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
            if action["on"] == "notProcessed" and item.processed:
                actions.remove(action)

        # Discard empty categories, separators
        remaining_actions = list()
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

                if action["__type__"] in ("category", "separator"):
                    try:
                        next_ = actions[index + 1]
                        if next_["__type__"] != "action":
                            isempty = True
                    except IndexError:
                        isempty = True

                if not isempty:
                    remaining_actions.append(action)

                index += 1

        return remaining_actions

    @QtCore.Slot(str)
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
            self.data["state"]["is_running"] = True

            item = self.data["models"]["item"].items[action["index"]]

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

            models = self.data["models"]

            self.data["state"]["is_running"] = False
            self.acted.emit()

            # Inform GUI of success or failure
            plugin = models["item"].plugins[result["plugin"]["id"]]
            plugin.actionPending = False
            plugin.actionHasError = not result["success"]

            # Allow running action upon action, without resetting
            models["result"].update_with_result(result)
            self.info.emit("Success" if result["success"] else "Failed")
            util.echo("Finished with states.. %s" % self.states)

        util.defer(run, callback=on_finished)

    @QtCore.Slot(int)
    def toggleInstance(self, index):
        models = self.data["models"]
        proxies = self.data["proxies"]

        qindex = proxies["instance"].index(index, 0, QtCore.QModelIndex())
        source_qindex = self.data["proxies"]["instance"].mapToSource(qindex)
        source_index = source_qindex.row()
        item = models["item"].items[source_index]

        if item.optional:
            self.__toggle_item(models["item"], source_index)
        else:
            self.error.emit("Cannot toggle")

    @QtCore.Slot(bool, str)
    def toggleSection(self, checkState, sectionLabel):
        model = self.data["models"]["item"]

        # Get all items' current toggle state
        states = set()
        for item in model.items:
            if item.itemType == "instance" and sectionLabel == item.category:
                if item.optional:
                    states.add(item.isToggled)

            if item.itemType == "plugin" and sectionLabel == item.verb:
                if item.optional:
                    states.add(item.isToggled)

        if len(states) == 1:
            # Use items' states instead of section state if all optional items
            # are the same state.
            checkState = not states.pop()

        for item in model.items:
            if item.itemType == "instance" and sectionLabel == item.category:
                if item.isToggled != checkState and item.optional:
                    self.__toggle_item(model, model.items.index(item))

            if item.itemType == "plugin" and sectionLabel == item.verb:
                if item.isToggled != checkState and item.optional:
                    self.__toggle_item(model, model.items.index(item))

    @QtCore.Slot(bool, str)
    def hideSection(self, hideState, sectionLabel):
        model = self.data["models"]["item"]

        for item in model.items:
            if item.itemType == "instance" and sectionLabel == item.category:
                self.__hide_item(model, model.items.index(item), hideState)

            if item.itemType == "plugin" and item.verb == sectionLabel:
                self.__hide_item(model, model.items.index(item), hideState)

            if item.itemType == "section" and item.name == sectionLabel:
                self.__hide_item(model, model.items.index(item), hideState)

    @QtCore.Slot(int, result="QVariant")
    def pluginData(self, index):
        models = self.data["models"]
        proxies = self.data["proxies"]

        qindex = proxies["plugin"].index(index, 0, QtCore.QModelIndex())
        source_qindex = proxies["plugin"].mapToSource(qindex)
        source_index = source_qindex.row()
        return self.__item_data(models["item"], source_index)

    @QtCore.Slot(int, result="QVariant")
    def instanceData(self, index):
        models = self.data["models"]
        proxies = self.data["proxies"]

        qindex = proxies["instance"].index(index, 0, QtCore.QModelIndex())
        source_qindex = proxies["instance"].mapToSource(qindex)
        source_index = source_qindex.row()
        return self.__item_data(models["item"], source_index)

    @QtCore.Slot(int)
    def togglePlugin(self, index):
        models = self.data["models"]
        proxies = self.data["proxies"]

        qindex = proxies["plugin"].index(index, 0, QtCore.QModelIndex())
        source_qindex = proxies["plugin"].mapToSource(qindex)
        source_index = source_qindex.row()
        item = models["item"].items[source_index]

        if item.optional:
            self.__toggle_item(self.data["models"]["item"], source_index)
        else:
            self.error.emit("Cannot toggle")

    @QtCore.Slot(str, str, str, str)
    def exclude(self, target, operation, role, value):
        """Exclude a `role` of `value` at `target`

        Arguments:
            target (str): Destination proxy model
            operation (str): "add" or "remove" exclusion
            role (str): Role to exclude
            value (str): Value of `role` to exclude

        """

        target = {"result": self.data["proxies"]["result"],
                  "instance": self.data["proxies"]["instance"],
                  "plugin": self.data["proxies"]["plugin"]}[target]

        if operation == "add":
            target.add_exclusion(role, value)

        elif operation == "remove":
            target.remove_exclusion(role, value)

        else:
            raise TypeError("operation must be either `add` or `remove`")

    @QtCore.Slot()
    def save(self):
        # Deprecated
        return

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

    def __hide_item(self, model, index, hideState):
        item = model.items[index]
        item.isHidden = hideState

    def __toggle_item(self, model, index):
        if "ready" not in self.states:
            return self.error.emit("Not ready")

        item = model.items[index]

        new_value = not item.isToggled
        old_value = item.isToggled

        if item.itemType == "plugin":
            self.host.emit("pluginToggled",
                           plugin=item.id,
                           new_value=new_value,
                           old_value=old_value)

        if item.itemType == "instance":
            self.host.emit("instanceToggled",
                           instance=item.id,
                           new_value=new_value,
                           old_value=old_value)

        item.isToggled = new_value
        self.data["models"]["item"].update_compatibility()

    def echo(self, data):
        """Append `data` to result model"""
        self.data["models"]["result"].add_item(data)

    def comment_sync(self, comment):
        """Update comments to host and notify subscribers"""
        self.host.update(key="comment", value=comment)
        self.host.emit("commented", comment=comment)

    def is_ready(self):
        count = self.data["state"]["readyCount"]
        util.wait(self.ready, 1000)
        return self.data["state"]["readyCount"] == count + 1

    # Event handlers

    def on_commenting(self, comment):
        """The user is entering a comment"""

        def update():
            context = self.host.cached_context
            context.data["comment"] = comment
            self.data["comment"] = comment

            # Notify subscribers of the comment
            self.comment_sync(comment)

            self.commented.emit()

        # Update local cache a little later
        util.schedule(update, 100, channel="commenting")

    def on_about_to_process(self, plugin, instance):
        """Reflect currently running pair in GUI"""

        if instance is None:
            instance_item = self.data["models"]["item"].instances[0]
        else:
            instance_item = self.data["models"]["item"].instances[instance.id]

        plugin_item = self.data["models"]["item"].plugins[plugin.id]

        for section in self.data["models"]["item"].sections:
            if section.name == plugin_item.verb:
                section.isProcessing = True
            if section.name == instance_item.category:
                section.isProcessing = True

        instance_item.isProcessing = True
        plugin_item.isProcessing = True

    def on_state_changed(self, state):
        util.echo("Entering state: \"%s\"" % state)

        if state == "ready":
            self.ready.emit()

        self.data["state"]["current"] = state
        self.data["state"]["all"] = list(
            s.name for s in self.machine.configuration()
        )

    def on_ready(self):
        self.data["state"]["readyCount"] += 1

    def on_finished(self):
        self.data["models"]["item"].reset_status()

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

    @QtCore.Slot()
    def stop(self):
        self.data["state"]["is_running"] = False
        self.stopping.emit()

    @QtCore.Slot()
    def reset(self):
        """Request that host re-discovers plug-ins and re-processes selectors

        A reset completely flushes the state of the GUI and reverts
        back to how it was when it first got launched.

        Pipeline:
              ______________     ____________     ______________
             |              |   |            |   |              |
             | host.reset() |-->| on_reset() |-->| on_context() |--
             |______________|   |____________|   |______________| |
             _______________     __________     _______________   |
            |               |   |          |   |               |  |
            | on_finished() |<--| on_run() |<--| on_discover() |<--
            |_______________|   |__________|   |_______________|

        """

        if not any(state in self.states for state in ("ready", "finished")):
            return self.error.emit("Not ready")

        self.initialising.emit()

        util.timer("resetting..")
        stats = {"requestCount": self.host.stats()["totalRequestCount"]}

        # Clear models
        self.data["models"]["item"].reset()
        self.data["models"]["result"].reset()

        def on_finished(plugins, context):
            # Compute compatibility
            for plugin in self.data["models"]["item"].plugins:
                if plugin.instanceEnabled:
                    instances = pyblish.logic.instances_by_plugin(context,
                                                                  plugin)
                    plugin.compatibleInstances = list(i.id for i in instances)
                else:
                    plugin.compatibleInstances = [context.id]

            self.data["models"]["item"].reorder(context)

            # Report statistics
            stats["requestCount"] -= self.host.stats()["totalRequestCount"]
            util.timer_end("resetting..", "Spent %.2f ms resetting")
            util.echo("Made %i requests during reset."
                      % abs(stats["requestCount"]))

            # Reset Context
            context_item = self.data["models"]["item"].instances[0]
            context_item.hasError = False
            context_item.succeeded = False
            context_item.processed = False
            context_item.isProcessing = False
            context_item.currentProgress = 0
            context_item.label = context.data.get("label")

            self.initialised.emit()

            self.data["models"]["item"].update_compatibility()

            # Remember comment across resets
            comment = self.data["comment"]
            if comment:
                print("Installing local comment..")
                self.host.cached_context.data["comment"] = comment
            else:
                print("No local comment, reading from context..")
                comment = self.host.cached_context.data.get("comment", "")
                self.data["comment"] = comment

            # Notify subscribers of the comment
            self.comment_sync(comment)

            first_run = self.data["firstRun"]
            if first_run:
                self.firstRun.emit()
                self.data["firstRun"] = False

            self.host.emit("reset", context=None)

            # Hidden sections
            for section in self.data["models"]["item"].sections:
                if section.name in settings.HiddenSections:
                    self.hideSection(True, section.name)

            # Run selected procedure on first run
            if first_run:
                if self.data.get('autoPublish'):
                    print("Starting auto-publish at first run..")
                    util.schedule(self.publish, 1)
                elif self.data.get('autoValidate'):
                    print("Starting auto-validate at first run..")
                    util.schedule(self.validate, 1)

        def on_run(plugins):
            """Fetch instances in their current state, right after reset"""

            util.defer(self.host.context,
                       callback=lambda context: on_finished(plugins, context))

        def on_discover(plugins, context):
            collectors = list()

            for plugin in plugins:
                self.data["models"]["item"].add_plugin(plugin.to_json())

                # Sort out which of these are Collectors
                if not pyblish.lib.inrange(
                        number=plugin.order,
                        base=pyblish.api.Collector.order):
                    continue

                if not plugin.active:
                    continue

                collectors.append(plugin)

            self.collecting.emit()

            self.run(collectors, context,
                     callback=on_run,
                     callback_args=[plugins])

        def on_context(context):
            context.data["pyblishQmlVersion"] = version
            context.data["targets"] = self.host.targets()

            self.data["models"]["item"].add_context(context.to_json())
            self.data["models"]["result"].add_context(context.to_json())

            util.defer(
                self.host.discover,
                callback=lambda plugins: on_discover(plugins, context)
            )

        def on_reset():
            util.defer(self.host.context, callback=on_context)

        util.defer(self.host.reset, callback=on_reset)

    @QtCore.Slot()
    def publish(self):
        """Start asynchonous publishing

        Publishing takes into account all available and currently
        toggled plug-ins and instances.

        """

        def get_data():
            model = self.data["models"]["item"]

            # Communicate with host to retrieve current plugins and instances
            # This can potentially take a very long time; it is run
            # asynchronously and initiates processing once complete.
            host_plugins = dict((p.id, p) for p in self.host.cached_discover)
            host_context = dict((i.id, i) for i in self.host.cached_context)

            plugins = list()
            instances = list()

            for plugin in models.ItemIterator(model.plugins):

                # Exclude Collectors
                if pyblish.lib.inrange(
                        number=plugin.order,
                        base=pyblish.api.Collector.order):
                    continue

                plugins.append(host_plugins[plugin.id])

            for instance in models.ItemIterator(model.instances):
                instances.append(host_context[instance.id])

            return plugins, instances

        def on_data_received(args):
            self.run(*args, callback=on_finished)

        def on_finished():
            self.host.emit("published", context=None)

            if not self.data["state"]["testPassed"]:
                # Possible stopped on validation fail or the extraction has
                # been interrupted. Depend on the continual processing test.
                return

            # If there are instance that has error after the test passed,
            # prompt publish failed message to footer.
            model = self.data["models"]["item"]
            for instance in models.ItemIterator(model.instances):
                if instance.hasError:
                    self.info.emit("Published, with errors..")
                    break

        util.defer(get_data, callback=on_data_received)

    @QtCore.Slot()
    def validate(self):
        """Start asynchonous validation

        Validation only takes into account currently available
        and toggled Validators, and leaves all else behind.

        """

        def get_data():
            model = self.data["models"]["item"]

            # Communicate with host to retrieve current plugins and instances
            # This can potentially take a very long time; it is run
            # asynchronously and initiates processing once complete.
            host_plugins = dict((p.id, p) for p in self.host.cached_discover)
            host_context = dict((i.id, i) for i in self.host.cached_context)

            plugins = list()
            instances = list()

            for plugin in models.ItemIterator(model.plugins):
                # Consider Validators only.
                if not pyblish.lib.inrange(plugin.order,
                                           base=pyblish.api.Validator.order):
                    continue

                plugins.append(host_plugins[plugin.id])

            for instance in models.ItemIterator(model.instances):
                instances.append(host_context[instance.id])

            return plugins, instances

        def on_data_received(args):
            self.run(*args, callback=on_finished)

        def on_finished():
            self.host.emit("validated", context=None)

        util.defer(get_data, callback=on_data_received)

    def run(self, plugins, context, callback=None, callback_args=None):
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
        callback_args = callback_args or []

        # if "ready" not in self.states:
        #     return self.error.emit("Not ready")

        # Initial set-up
        self.data["state"]["is_running"] = True

        # Setup statistics for better debugging.
        # (To be finalised in `on_finished`)
        util.timer("publishing")
        stats = {"requestCount": self.host.stats()["totalRequestCount"]}

        # For each completed task, update
        # the GUI and commence next task.
        def on_next(result):
            if isinstance(result, StopIteration):
                return on_finished(str(result))

            self.data["models"]["item"].update_with_result(result)
            self.data["models"]["result"].update_with_result(result)

            # Once the main thread has finished updating
            # the GUI, we can proceed handling of next task.
            util.defer(self.host.context, callback=update_context)

        def update_context(ctx):
            item_model = self.data["models"]["item"]
            instance_items = {item.id: item for item in item_model.instances}
            for instance in ctx:
                id = instance.id
                item = instance_items.get(id)
                if item is not None:
                    proxy = next((i for i in context if i.id == id), None)
                    update_instance(item, proxy, instance.data)
                    continue

                context.append(instance)
                item_model.add_instance(instance.to_json())

            if len(ctx) < item_model.instance_count():
                remove_instance(ctx, instance_items)

            util.defer(lambda: next(iterator), callback=on_next)

        def update_instance(item, proxy, data):
            """Update model and proxy for reflecting changes on instance"""

            # Update instance item model data for GUI
            item.isToggled = data.get("publish", True)
            item.optional = data.get("optional", True)
            item.category = data.get("category", data["family"])
            item.label = data.get("label", None)

            families = [data["family"]]
            families.extend(data.get("families", []))
            item.familiesConcatenated = ", ".join(families)

            if proxy is None:
                return
            # Update proxy instance data which currently being iterated in
            # the primary iterator
            proxy.data["publish"] = data.get("publish", True)
            proxy.data["family"] = data["family"]
            proxy.data["families"] = data.get("families", [])

        def remove_instance(ctx, items):
            """Remove instance"""
            instances = {i.id: i for i in context}
            instance_ids = set(i.id for i in ctx)
            instance_ids.add(ctx.id)
            for id, item in items.items():
                if id not in instance_ids:
                    # Remove from model
                    self.data["models"]["item"].remove_instance(item)
                    # Remove instance from list
                    context.remove(instances[id])

        def on_finished(message=None):
            """Locally running function"""
            self.data["state"]["is_running"] = False
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
        util.defer(lambda: next(iterator), callback=on_next)

    @QtCore.Slot(int)
    def repairPlugin(self, index):
        """

        DEPRECATED: REMOVE ME

        """

        if "finished" not in self.states:
            self.error.emit("Not ready")
            return

        self.data["state"]["is_running"] = True

        # Setup statistics
        util.timer("publishing")
        stats = {"requestCount": self.host.stats()["totalRequestCount"]}

        instance_iterator = models.ItemIterator(
            self.data["models"]["item"].instances)
        failed_instances = [p.id for p in instance_iterator
                            if p.hasError]

        # Get available items from host
        plugins = collections.OrderedDict(
            (p.id, p) for p in self.host.discover())
        context = collections.OrderedDict(
            (p.id, p) for p in self.host.context()
            if p.id in failed_instances)

        # Filter items in GUI with items from host
        index = self.data["proxies"]["plugin"].index(
            index, 0, QtCore.QModelIndex())
        index = self.data["proxies"]["plugin"].mapToSource(index)
        plugin = self.data["models"]["item"].items[index.row()]
        plugin.hasError = False

        plugin = plugins[plugin.id]

        iterator = pyblish.logic.process(
            func=self.host.repair,
            plugins=[plugin],
            context=context.values(),
            test=self.host.test)

        def on_next(result):
            if not self.data["state"]["is_running"]:
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

            self.data["models"]["item"].update_with_result(result)
            self.data["models"]["result"].update_with_result(result)

            # Run next again
            util.defer(lambda: next(iterator), callback=on_next)

        def on_finished():
            self.data["state"]["is_running"] = False
            self.finished.emit()

            # Report statistics
            stats["requestCount"] -= self.host.stats()["totalRequestCount"]
            util.timer_end("publishing", "Spent %.2f ms resetting")
            util.echo("Made %i requests during publish."
                      % abs(stats["requestCount"]))

        # Reset state
        util.defer(lambda: next(iterator), callback=on_next)


def iterator(plugins, context):
    """An iterator for plug-in and instance pairs"""
    test = pyblish.logic.registered_test()
    state = {
        "nextOrder": None,
        "ordersWithError": set()
    }

    for plugin in plugins:
        state["nextOrder"] = plugin.order

        message = test(**state)
        if message:
            return StopIteration("Stopped due to %s" % message)

        instances = pyblish.api.instances_by_plugin(context, plugin)
        if plugin.__instanceEnabled__:
            for instance in instances:
                yield plugin, instance

        else:
            yield plugin, None
