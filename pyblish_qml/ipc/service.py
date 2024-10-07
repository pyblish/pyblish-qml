
import os
import sys
import time
import getpass
import logging
import traceback

import pyblish.api
import pyblish.lib
import pyblish.plugin

from . import mocking, formatting

_log = logging.getLogger("pyblish-qml")


def IdList(items):
    return pyblish.lib.ItemList("id", items)


class Service(object):
    _count = 0
    __instances = property(lambda self: IdList(self._context))
    __plugins = property(lambda self: IdList(self._plugins))

    def __init__(self):
        self._context = None
        self._plugins = None
        self._provider = None
        self._post_collect = None

        self.reset()

    def test(self, **vars):
        test = pyblish.logic.registered_test()

        # -> Support test, see #364
        vars["ordersWithError"] = set(vars["ordersWithError"])

        return test(**vars)

    def ping(self):
        """Used to check connectivity"""
        return {
            "message": "Hello, whomever you are"
        }

    def stats(self):
        """Return statistics about the API"""
        return {
            "totalRequestCount": self._count,
        }

    def reset(self):
        self._context = pyblish.api.Context()
        self._plugins = pyblish.api.discover()
        self._provider = pyblish.plugin.Provider()
        self._post_collect = formatting.format_post_collect_order(
            os.environ.get("PYBLISH_QML_POST_COLLECT"))

    def context(self):
        # Append additional metadata to context
        port = os.environ.get("PYBLISH_CLIENT_PORT", -1)
        hosts = ", ".join(reversed(pyblish.api.registered_hosts()))

        for key, value in {"host": hosts,
                           "port": int(port),
                           "user": getpass.getuser(),
                           "postCollectOrder": self._post_collect,
                           "connectTime": pyblish.lib.time(),
                           "pyblishVersion": pyblish.version,
                           "pythonVersion": sys.version}.items():

            self._context.data[key] = value

        return formatting.format_context(self._context)

    def discover(self):
        return formatting.format_plugins(self._plugins)

    def process(self, plugin, instance=None, action=None):
        """Given JSON objects from client, perform actual processing

        Arguments:
            plugin (dict): JSON representation of plug-in to process
            instance (dict, optional): JSON representation of Instance to
                be processed.
            action (str, optional): Id of action to process

        """

        plugin_obj = self.__plugins[plugin["id"]]
        instance_obj = (self.__instances[instance["id"]]
                        if instance is not None else None)

        result = pyblish.plugin.process(
            plugin=plugin_obj,
            context=self._context,
            instance=instance_obj,
            action=action)

        return formatting.format_result(result)

    def repair(self, plugin, instance=None):
        plugin_obj = self.__plugins[plugin["id"]]
        instance_obj = (self.__instances[instance["id"]]
                        if instance is not None else None)

        result = pyblish.plugin.repair(
            plugin=plugin_obj,
            context=self._context,
            instance=instance_obj)

        return formatting.format_result(result)

    def _dispatch(self, method, params):
        """Customise exception handling"""
        self._count += 1

        func = getattr(self, method)
        try:
            return func(*params)
        except Exception as e:
            traceback.print_exc()
            raise e

    def emit(self, signal, kwargs):
        """Trigger registered callbacks

        This method is triggered remotely and run locally.
        The keywords "instance" and "plugin" are implicitly
        converted to their corresponding Pyblish objects.

        """

        if "context" in kwargs:
            kwargs["context"] = self._context

        if "instance" in kwargs:
            kwargs["instance"] = self.__instances[kwargs["instance"]]

        if "plugin" in kwargs:
            kwargs["plugin"] = self.__plugins[kwargs["plugin"]]

        pyblish.api.emit(signal, **kwargs)

    def update(self, key, value, name):
        """Write data to context from GUI"""
        context = self._context
        if name == "Context":
            context.data[key] = value
        else:
            instance = next(it for it in context if name == it.name)
            instance.data[key] = value


class MockService(Service):
    def __init__(self, delay=0.01, *args, **kwargs):
        super(MockService, self).__init__(*args, **kwargs)
        self.delay = delay

    def discover(self):
        return formatting.format_plugins(mocking.plugins)

    def reset(self):
        self._context = pyblish.api.Context()
        self._plugins = IdList(mocking.plugins)
        self._provider = pyblish.plugin.Provider()

    def process(self, *args, **kwargs):
        time.sleep(self.delay)
        return super(MockService, self).process(*args, **kwargs)
