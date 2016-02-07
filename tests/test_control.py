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

from . import lib

# Module-level setup and teardown
setup = lib._setup
teardown = lib._teardown


def check_present(name, model):
    assert_in(name, [i.name for i in model.items])


def reset(controller=None):
    if controller is None:
        controller = control.Controller()
        controller.on_client_changed(lib.port)

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
        controller.on_client_changed(lib.port)

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
        controller.on_client_changed(lib.port)

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

    count = {"#": 0}

    class MyCollector(pyblish.api.Collector):
        def process(self, context):
            instance = context.create_instance("MyInstance")
            instance.set_data("family", "myFamily")
            count["#"] += 1

    pyblish.api.register_plugin(MyCollector)

    c = reset()

    # At this point, the item-model is populated with
    # a number of instances.
    check_present("MyCollector", c.item_model)
    check_present("MyInstance", c.item_model)
    assert_equals(count["#"], 1)


@with_setup(lib.clean)
def test_publish():
    """Publishing works"""

    count = {"#": 0}

    class Collector(pyblish.api.Collector):
        def process(self, context):
            instance = context.create_instance("MyInstance")
            instance.set_data("family", "myFamily")
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


@with_setup(lib._setup, lib._teardown)
def test_publish_only_toggled():
    """Only toggled items are published"""

    count = {"#": 0}

    class MyCollector(pyblish.api.Collector):
        def process(self, context):
            instance = context.create_instance("MyInstance")
            instance.set_data("family", "myFamily")
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

    c.item_model.plugins["MyValidator"].isToggled = False

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
