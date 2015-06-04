import pyblish.api

from pyblish_qml import control

import lib

# Vendor libraries
from nose.tools import *

from PyQt5 import QtTest


def check_present(name, model):
    assert_in(name, [i.name for i in model.items])


def reset(controller=None):
    c = controller or control.Controller()
    c.on_client_changed(lib.port)

    ready = QtTest.QSignalSpy(c.ready)

    assert_true(ready.wait(1000))

    count = len(ready)
    c.reset()

    ready.wait(1000)
    assert_equals(len(ready), count + 1)
    assert_true("ready" in c.states)

    return c


def publish(controller=None):
    """Publish current state

    Argument:
        plugins (list): List of plug-ins to include
        plugin (str): Name of plug-in to repair

    """

    c = controller or control.Controller()
    c.on_client_changed(lib.port)

    finished = QtTest.QSignalSpy(c.finished)

    count = len(finished)
    c.publish()

    finished.wait(1000)
    assert_equals(len(finished), count + 1)
    assert_true("finished" in c.states)

    return c


def repair_plugin(plugin, controller=None):
    """Repair single plug-in

    Argument:
        plugins (list): List of plug-ins to include
        plugin (str): Name of plug-in to repair

    """

    c = controller or control.Controller()

    finished = QtTest.QSignalSpy(c.finished)

    count = len(finished)
    c.repairPlugin(index)

    finished.wait(1000)
    assert_equals(len(finished), count + 1)
    assert_true("finished" in c.states)

    return c


@with_setup(lib._setup, lib._teardown)
def test_reset():
    """Reset works"""

    count = {"#": 0}

    class Selector(pyblish.api.Selector):
        def process(self, context):
            instance = context.create_instance("MyInstance")
            instance.set_data("family", "myFamily")
            count["#"] += 1

    pyblish.api.register_plugin(Selector)

    c = reset()

    # At this point, the item-model is populated with
    # a number of instances.

    check_present("Selector", c.item_model)
    check_present("MyInstance", c.item_model)
    assert_equals(count["#"], 1)


@with_setup(lib._setup, lib._teardown)
def test_publish():
    """Publishing works"""

    count = {"#": 0}

    class Selector(pyblish.api.Selector):
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

    plugins = [Selector, Validator, Extractor]

    for plugin in plugins:
        pyblish.api.register_plugin(plugin)

    c = reset()

    check_present("Selector", c.item_model)
    check_present("MyInstance", c.item_model)
    assert_equals(count["#"], 1)

    # At this point, the item-model is populated with
    # a number of instances.

    publish(controller=c)

    names = [p.__name__ for p in plugins]
    inmodel = [p.name for p in c.item_model.plugins]

    assert_true(all(n in inmodel for n in names))
    assert_equals(len(c.host.context()), 1)
    assert_equals(count["#"], 111)


@with_setup(lib._setup, lib._teardown)
def test_publish_only_toggled():
    """Only toggled items are published"""

    count = {"#": 0}

    class Selector(pyblish.api.Selector):
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

    plugins = [Selector, Validator, Extractor]

    for plugin in plugins:
        pyblish.api.register_plugin(plugin)

    c = reset()

    check_present("Selector", c.item_model)
    check_present("MyInstance", c.item_model)

    c.item_model.plugins["Validator"].isToggled = False

    publish(c)

    assert_equals(count["#"], 101)
