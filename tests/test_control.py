import pyblish.api

from pyblish_qml import control
from pyblish_qml import models

import lib

# Vendor libraries
from nose.tools import *

from PyQt5 import QtTest


def _setup():
    lib._setup()


def _teardown():
    lib._teardown()


def reset(controller=None):
    c = controller or control.Controller(lib.port)

    ready = QtTest.QSignalSpy(c.ready)
    finished = QtTest.QSignalSpy(c.finished)

    assert_true(ready.wait(1000))

    count = len(finished)
    c.reset()

    finished.wait(1000)
    assert_equals(len(finished), count + 1)
    assert_equals([p.name for p in c.item_model.plugins], plugins)
    assert_true("ready" in c.states)

    return c


def publish(controller=None):
    """Publish current state

    Argument:
        plugins (list): List of plug-ins to include
        plugin (str): Name of plug-in to repair

    """

    c = controller or Controller()

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

    c = controller or Controller()

    finished = QtTest.QSignalSpy(c.finished)

    count = len(finished)
    c.repairPlugin(index)

    finished.wait(1000)
    assert_equals(len(finished), count + 1)
    assert_true("finished" in c.states)

    return c


@with_setup(_setup, _teardown)
def test_reset():
    """Reset works"""

    count = {"#": 0}

    class Selector(pyblish.api.Selector):
        def process(self, context):
            instance = context.create_instance("MyInstance")
            instance.set_data("family", "myFamily")
            count["#"] += 1

    class Validator(pyblish.api.Validator):
        def process(self, instance):
            count["#"] += 1

    class Extractor(pyblish.api.Extractor):
        def process(self, instance):
            count["#"] += 1

    plugins = [Selector, Validator, Extractor]

    for plugin in plugins:
        pyblish.api.register_plugin(plugin)

    c = reset()

    # At this point, the item-model is populated with
    # a number of instances.

    assert_true(all([p.name in c.item_model.plugins
                    for p in [_p.name for _p in plugins]]))

    assert_equals(count["#"], 3)
    assert_equals(len(c.host.context()), 1)


@with_setup(_setup, _teardown)
def test_publish():
    """Publishing works"""
    plugins = ["Selector1", "Validator1", "Extractor1"]

    c = reset(plugins)

    publish(plugins, controller=c)

    # Publishing has finished; the item-model
    # should now contain plug-ins with their
    # `succeeded` flag set to True

    for plugin, instance in models.ItemIterator(c.item_model):
        print "# %s->%s" % (plugin, instance)
        assert_true(plugin.succeeded)
        assert_true(instance.succeeded)


@with_setup(_setup, _teardown)
def test_publish_only_toggled():
    plugins = ["Selector1", "Validator1", "Extractor1"]

    c = reset(plugins)

    for plugin in c.item_model.plugins:
        if plugin.name == "Validator1":
            plugin.isToggled = False

    publish(plugins, c)

    plugin = c.item_model.plugins["Validator1"]
    assert_false(plugin.processed)
    plugin = c.item_model.plugins["Extractor1"]
    assert_true(plugin.processed)


@with_setup(_setup, _teardown)
def test_publish_only_compatible():
    plugins = ["Selector1", "ValidatorIncompatible", "Extractor1"]

    c = reset(plugins)

    plugin = c.item_model.plugins["ValidatorIncompatible"]
    assert_false(plugin.hasCompatible)

    plugin = c.item_model.plugins["Extractor1"]
    assert_true(plugin.hasCompatible)

    publish(plugins, c)

    plugin = c.item_model.plugins["ValidatorIncompatible"]
    assert_false(plugin.processed)

    plugin = c.item_model.plugins["Extractor1"]
    assert_true(plugin.processed)


@with_setup(_setup, _teardown)
def test_publish_failure():
    """Publishing with failure"""
    plugins = ["Selector1", "Validator1", "ExtractorFails"]

    c = reset(plugins)

    publish(plugins, controller=c)

    # Publishing has finished; the item-model
    # should now contain plug-ins with their
    # `succeeded` flag set to True

    for plugin, instance in models.ItemIterator(c.item_model):
        if plugin.name == "ExtractorFails":
            assert_false(plugin.succeeded)
        else:
            assert_true(plugin.succeeded)


@with_setup(_setup, _teardown)
def test_state_equals_last_entered():
    """State property of controller equals the last entered state"""
    plugins = ["Selector1", "Validator1", "Extractor1"]

    c = reset(plugins)

    _state = {}

    def on_state_changed(state):
        _state["current"] = state

    c.state_changed.connect(on_state_changed)

    publish(plugins, controller=c)

    assert_equals(c.state, _state["current"])


@with_setup(_setup, _teardown)
def test_pyqt_properties():
    """pyqtPropeties provide attributes properly"""
    c = Controller()

    assert_equals(c.instanceProxy, c.instance_proxy)
    assert_equals(c.pluginProxy, c.plugin_proxy)
    assert_equals(c.resultProxy, c.result_proxy)
    assert_equals(c.resultModel, c.result_model)


@with_setup(_setup, _teardown)
def test_repair_instance():
    """Repairing an instance works"""


@with_setup(_setup, _teardown)
def test_repair_context():
    """Repairing the context works"""
