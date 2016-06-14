from PyQt5 import QtTest

# Vendor libraries
from nose.tools import (
    assert_in,
    assert_true,
    assert_equals,
    with_setup
)

from pyblish_qml import control
import pyblish.api

from . import port, lib


def check_present(name, model):
    assert_in(name, [i.name for i in model.items])


def reset(controller=None):
    if controller is None:
        controller = control.Controller()
        controller.on_client_changed(port)

    ready = QtTest.QSignalSpy(controller.ready)

    assert_true(ready.wait(1000))

    count = len(ready)
    controller.reset()

    ready.wait(1000)
    assert_equals(len(ready), count + 1)
    assert_true("ready" in controller.states)

    return controller


def publish(controller=None):
    """Publish current state

    Argument:
        plugins (list): List of plug-ins to include
        plugin (str): Name of plug-in to repair

    """

    if controller is None:
        controller = control.Controller()
        controller.on_client_changed(port)

    finished = QtTest.QSignalSpy(controller.finished)

    count = len(finished)
    controller.publish()

    finished.wait(1000)
    assert_equals(len(finished), count + 1)
    assert_true("finished" in controller.states)

    return controller


def validate(controller=None):
    """Publish current state

    Argument:
        plugins (list): List of plug-ins to include
        plugin (str): Name of plug-in to repair

    """

    if controller is None:
        controller = control.Controller()
        controller.on_client_changed(port)

    finished = QtTest.QSignalSpy(controller.finished)

    count = len(finished)
    controller.validate()

    finished.wait(1000)
    assert_equals(len(finished), count + 1)
    assert_true("finished" in controller.states)

    return controller


@with_setup(lib.clean)
def test_reset():
    """Reset works"""

    data = {"#": 0, "instances": list()}

    class MyCollector(pyblish.api.Collector):
        def process(self, context):
            instance = context.create_instance("MyInstance")
            instance.data["family"] = "myFamily"
            data["#"] += 1
            data["instances"].append(instance)

    pyblish.api.register_plugin(MyCollector)

    c = reset()

    # At this point, the item-model is populated with
    # a number of instances.
    check_present("MyCollector", c.item_model)
    check_present(data["instances"][0].name, c.item_model)
    assert_equals(data["#"], 1)


@with_setup(lib.clean)
def test_publish():
    """Publishing works"""

    count = {"#": 0}

    class Collector(pyblish.api.Collector):
        def process(self, context):
            instance = context.create_instance("MyInstance")
            instance.data["family"] = "myFamily"
            count["#"] += 1

    class Validator(pyblish.api.Validator):
        def process(self, instance):
            count["#"] += 10

    class Extractor(pyblish.api.Extractor):
        def process(self, instance):
            count["#"] += 100

    plugins = [Collector, Validator, Extractor]

    for plugin in plugins:
        pyblish.api.register_plugin(plugin)

    c = reset()

    check_present("Collector", c.item_model)
    check_present("MyInstance", c.item_model)
    assert_equals(count["#"], 1)

    # At this point, the item-model is populated with
    # a number of instances.

    publish(c)

    names = [p.__name__ for p in plugins]
    inmodel = [p.name for p in c.item_model.plugins]

    assert_true(all(n in inmodel for n in names))
    assert_equals(len(c.host.context()), 1)
    assert_equals(count["#"], 111)


@with_setup(lib.clean)
def test_publish_only_toggled():
    """Only toggled items are published"""

    count = {"#": 0}

    class MyCollector(pyblish.api.Collector):
        def process(self, context):
            instance = context.create_instance("MyInstance")
            instance.data["family"] = "myFamily"
            count["#"] += 1

    class MyValidator(pyblish.api.Validator):
        def process(self, instance):
            count["#"] += 10

    class MyExtractor(pyblish.api.Extractor):
        def process(self, instance):
            count["#"] += 100

    plugins = [MyCollector, MyValidator, MyExtractor]

    for plugin in plugins:
        pyblish.api.register_plugin(plugin)

    c = reset()

    check_present("MyCollector", c.item_model)
    check_present("MyInstance", c.item_model)

    c.item_model.plugins[MyValidator.id].isToggled = False

    publish(c)

    assert_equals(count["#"], 101)


@with_setup(lib.clean)
def test_cooperative_collection():
    """Cooperative collection works

    A collector should be able to run such that the following
    collector "sees" the newly created instance so as to
    query and/or modify it.

    """

    history = []
    count = {"#": 0}

    class CollectorA(pyblish.api.Collector):
        order = 0.0

        def process(self, context):
            context.create_instance("myInstance1")
            history.append(type(self).__name__)
            count["#"] += 1

    class CollectorB(pyblish.api.Collector):
        order = 0.1

        def process(self, context):
            assert "myInstance1" in [i.data["name"] for i in context]

            # This should run
            history.append(type(self).__name__)
            count["#"] += 10

            context.create_instance("myInstance2")

    pyblish.api.register_plugin(CollectorA)
    pyblish.api.register_plugin(CollectorB)

    c = reset()

    check_present("CollectorA", c.item_model)
    check_present("CollectorB", c.item_model)
    check_present("myInstance1", c.item_model)
    check_present("myInstance2", c.item_model)

    assert count["#"] == 11, count
    assert history == ["CollectorA", "CollectorB"]


@with_setup(lib.clean)
def test_argumentless_plugin():
    """Implicit plug-ins without arguments should still run"""
    count = {"#": 0}

    class MyPlugin(pyblish.api.Validator):
        def process(self):
            count["#"] += 1

    pyblish.api.register_plugin(MyPlugin)

    c = reset()
    publish(c)

    check_present("MyPlugin", c.item_model)

    assert count["#"] == 1


@with_setup(lib.clean)
def test_cooperative_collection2():
    """Cooperative collection works with InstancePlugin"""

    count = {"#": 0}
    history = []

    class CollectorA(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder

        def process(self, context):
            history.append(type(self).__name__)
            context.create_instance("MyInstance")
            count["#"] += 1

    class CollectorB(pyblish.api.InstancePlugin):
        order = pyblish.api.CollectorOrder + 0.1

        def process(self, instance):
            history.append(type(self).__name__)
            count["#"] += 10

    pyblish.api.register_plugin(CollectorA)
    pyblish.api.register_plugin(CollectorB)

    c = reset()

    check_present("CollectorA", c.item_model)
    check_present("CollectorB", c.item_model)
    check_present("MyInstance", c.item_model)

    assert count["#"] == 11, count
    assert history == ["CollectorA", "CollectorB"]


@with_setup(lib.clean)
def test_published_event():
    """published is emitted upon finished publish"""

    count = {"#": 0}

    def on_published(context):
        assert isinstance(context, pyblish.api.Context)
        count["#"] += 1

    pyblish.api.register_callback("published", on_published)

    c = reset()
    publish(c)

    assert count["#"] == 1, count


@with_setup(lib.clean)
def test_validated_event():
    """validated is emitted upon finished validation"""

    count = {"#": 0}

    def on_validated(context):
        assert isinstance(context, pyblish.api.Context)
        count["#"] += 1

    pyblish.api.register_callback("validated", on_validated)

    c = reset()
    validate(c)

    assert count["#"] == 1, count


@with_setup(lib.clean)
def test_gui_vs_host_order():
    """Host properly reflects order of instances in GUI"""

    instances = [
        "instance4",
        "instance3",
        "instance2",
        "instance1"
    ]

    class Collector(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder

        def process(self, context):
            for name in instances:
                context.create_instance(name)

    class SortByName(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder + 0.1

        def process(self, context):
            context[:] = sorted(context, key=lambda i: i.name)

    pyblish.api.register_plugin(Collector)

    # Test baseline
    c = reset()

    gui_instances = list(
        i.name for i in c.item_model.instances
        if i.name != "Context"
    )

    # GUI should contain the original order
    assert gui_instances == instances, "QML has got a different order"

    host_instances = list(i.name for i in c.host.context())

    # Host should also contain the original order
    assert host_instances == instances, "Host has got a different order"

    # Sort context retrospectively
    pyblish.api.register_plugin(SortByName)
    c = reset()

    gui_instances = list(
        i.name for i in c.item_model.instances
        if i.name != "Context"
    )

    host_instances = list(i.name for i in c.host.context())

    # GUI should reflect sorted order
    print("gui_instances: %s" % gui_instances)
    assert gui_instances != instances, "Sorting did not happen in QML"

    print("host_instances: %s" % host_instances)
    assert host_instances != instances, "Sorting did not happen in host"

    assert gui_instances == host_instances, "QML != Host"


@with_setup(lib.clean)
def test_toggle_compatibility():
    """toggle instance updates compatibility correctly"""

    data = {"instance": None}

    class Collector(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder

        def process(self, context):
            instance = context.create_instance("A")
            instance.data["family"] = "FamilyA"
            data['instance'] = instance

    class Validate(pyblish.api.InstancePlugin):
        """A dummy validator"""
        order = pyblish.api.ValidatorOrder
        families = ["FamilyA"]

        def process(self, instance):
            pass

    pyblish.api.register_plugin(Collector)
    pyblish.api.register_plugin(Validate)

    c = reset()

    def has_enabled_validator(c):
        """Return whether Validate validator is enabled/compatible"""

        rows = c.plugin_proxy.rowCount()
        for row in range(rows):
            item = c.plugin_proxy.item(row)
            if item.name == 'Validate':
                return True

        return False

    item = c.item_model.instances[data['instance'].id]
    index = c.item_model.items.index(item)

    # Default state (enabled)
    assert has_enabled_validator(c), "Not enabled before"

    # toggle off
    c.toggleInstance(index)
    assert not has_enabled_validator(c), "Not disabled"

    # toggle back on
    c.toggleInstance(index)
    assert has_enabled_validator(c), "Not enabled after"


@with_setup(lib.clean)
def test_action_on_failed():
    """Actions on failed are exclusive to plug-ins that have failed"""

    class SelectMany(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder

        def process(self, context):
            for name in ("A", "B", "C"):
                context.create_instance(name)

    class ActionOnFailed(pyblish.api.Action):
        on = "failed"

    class ValidateFail(pyblish.api.InstancePlugin):
        order = pyblish.api.ValidatorOrder
        actions = [ActionOnFailed]

        def process(self, instance):
            assert False

    class ValidateSuccess(pyblish.api.InstancePlugin):
        order = pyblish.api.ValidatorOrder
        actions = [ActionOnFailed]

        def process(self, instance):
            assert True

    pyblish.api.register_plugin(SelectMany)
    pyblish.api.register_plugin(ValidateFail)
    pyblish.api.register_plugin(ValidateSuccess)

    c = reset()

    validate_fail_index = c.item_model.items.index(
        c.item_model.plugins[ValidateFail.id])
    validate_success_index = c.item_model.items.index(
        c.item_model.plugins[ValidateSuccess.id])

    validate_fail_actions = c.getPluginActions(validate_fail_index)

    assert not validate_fail_actions, (
        "ValidateFail should not have produced any actions")

    validate(c)

    validate_fail_actions = c.getPluginActions(validate_fail_index)

    assert len(validate_fail_actions) == 1, (
        "ValidateFail should have had an action")
    assert validate_fail_actions[0]["id"] == ActionOnFailed.id, (
        "ValidateFail had an unknown action")

    validate_success_actions = c.getPluginActions(validate_success_index)
    assert len(validate_success_actions) == 0, (
        "ValidateSuccess should not have had an action")


@with_setup(lib.clean)
def test_action_not_processed():
    """Actions on not processed """

    class SelectMany(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder

        def process(self, context):
            for name in ("A", "B", "C"):
                context.create_instance(name)

    class ActionOnNotProcessed(pyblish.api.Action):
        on = "notProcessed"

    class ValidateAction(pyblish.api.InstancePlugin):
        order = pyblish.api.ValidatorOrder
        actions = [ActionOnNotProcessed]

        def process(self, instance):
            assert True

    pyblish.api.register_plugin(SelectMany)
    pyblish.api.register_plugin(ValidateAction)

    c = reset()

    validate_index = c.item_model.items.index(
        c.item_model.plugins[ValidateAction.id])

    validate_actions = c.getPluginActions(validate_index)

    assert len(validate_actions) == 1, (
        "ValidateAction should have 1 action")

    validate(c)

    validate_actions = c.getPluginActions(validate_index)

    assert len(validate_actions) == 0, (
        "ValidateAction should not have had an action")


def test_inactive_collector():
    """An inactive collector should not run"""

    count = {"#": 0}

    class MyInactiveCollector(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder
        active = False

        def process(self, context):
            print("Ran %s" % type(self))
            count["#"] += 1

    class MyActiveCollector(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder
        active = True

        def process(self, context):
            print("Ran %s" % type(self))
            count["#"] += 10

    pyblish.api.register_plugin(MyInactiveCollector)
    pyblish.api.register_plugin(MyActiveCollector)

    reset()

    assert count["#"] == 10
