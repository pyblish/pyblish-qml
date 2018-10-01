"""Speak to parent process"""

import os
import sys
import json
import threading

import pyblish.api
import pyblish.plugin

from ..vendor import six
from ..vendor.six.moves import queue


class Proxy(object):
    """Messages sent from QML to parent process"""

    channels = {
        "response": queue.Queue(),
        "parent": queue.Queue(),
    }

    def __init__(self):
        self.cached_context = list()
        self.cached_discover = list()

        self._self_destruct()
        self._listen()

    def stats(self):
        return self._dispatch("stats")

    def reset(self):
        return self._dispatch("reset")

    def detach(self):
        self._dispatch("detach")

    def attach(self, qRect):
        geometry = [qRect.x(), qRect.y(), qRect.width(), qRect.height()]
        self._dispatch("attach", args=geometry)

    def popup(self, alert):
        self._dispatch("popup", args=[alert])

    def test(self, **vars):
        """Vars can only be passed as a non-keyword argument"""
        return self._dispatch("test", kwargs=vars)

    def ping(self):
        self._dispatch("ping", args=[])
        return True

    def process(self, plugin, context, instance=None, action=None):
        """Transmit a `process` request to host

        Arguments:
            plugin (PluginProxy): Plug-in to process
            context (ContextProxy): Filtered context
            instance (InstanceProxy, optional): Instance to process
            action (str, optional): Action to process

        """

        plugin = plugin.to_json()
        instance = instance.to_json() if instance is not None else None
        return self._dispatch("process", args=[plugin, instance, action])

    def repair(self, plugin, context, instance=None):
        plugin = plugin.to_json()
        instance = instance.to_json() if instance is not None else None
        return self._dispatch("repair", args=[plugin, instance])

    def context(self):
        self.cached_context = ContextProxy.from_json(self._dispatch("context"))
        return self.cached_context

    def discover(self):
        self.cached_discover[:] = list()
        for plugin in self._dispatch("discover"):
            self.cached_discover.append(PluginProxy.from_json(plugin))

        return self.cached_discover

    def emit(self, signal, **kwargs):
        self._dispatch("emit", args=[signal, kwargs])

    def update(self, key, value):
        self._dispatch("update", args=[key, value])

    def _self_destruct(self):
        """Auto quit exec if parent process failed
        """
        # This will give parent process 15 seconds to reset.
        self._kill = threading.Timer(15, lambda: os._exit(0))
        self._kill.start()

    def _listen(self):
        """Listen for messages passed from parent

        This method distributes messages received via stdin to their
        corresponding channel. Based on the format of the incoming
        message, the message is forwarded to its corresponding channel
        to be processed by its corresponding handler.

        """

        def _listen():
            """This runs in a thread"""
            for line in iter(sys.stdin.readline, b""):
                try:
                    response = json.loads(line)

                except Exception as e:
                    # The parent has passed on a message that
                    # isn't formatted in any particular way.
                    # This is likely a bug.
                    raise e

                else:
                    if response.get("header") == "pyblish-qml:popen.response":
                        self.channels["response"].put(line)

                    elif response.get("header") == "pyblish-qml:popen.parent":
                        self.channels["parent"].put(line)

                    elif response.get("header") == "pyblish-qml:server.pulse":
                        self._kill.cancel()  # reset timer
                        self._self_destruct()

                    else:
                        # The parent has passed on a message that
                        # is JSON, but not in any format we recognise.
                        # This is likely a bug.
                        raise Exception("Unhandled message "
                                        "passed to Popen, '%s'" % line)

        thread = threading.Thread(target=_listen)
        thread.daemon = True
        thread.start()

    def _dispatch(self, func, args=None):
        """Send message to parent process

        Arguments:
            func (str): Name of function for parent to call
            args (list, optional): Arguments passed to function when called

        """

        data = json.dumps(
            {
                "header": "pyblish-qml:popen.request",
                "payload": {
                    "name": func,
                    "args": args or list(),
                }
            }
        )

        # This should never happen. Each request is immediately
        # responded to, always. If it isn't the next line will block.
        # If multiple responses were made, then this will fail.
        # Both scenarios are bugs.
        assert self.channels["response"].empty(), (
            "There were pending messages in the response channel")

        sys.stdout.write(data + "\n")
        sys.stdout.flush()

        try:
            message = self.channels["response"].get()

            if six.PY3:
                response = json.loads(message)
            else:
                response = _byteify(json.loads(message, object_hook=_byteify))

        except TypeError as e:
            raise e

        else:
            assert response["header"] == "pyblish-qml:popen.response", response
            return response["payload"]


def _byteify(data):
    """Convert unicode to bytes"""

    # Unicode
    if isinstance(data, six.text_type):
        return data.encode("utf-8")

    # Members of lists
    if isinstance(data, list):
        return [_byteify(item) for item in data]

    # Members of dicts
    if isinstance(data, dict):
        return {
            _byteify(key): _byteify(value) for key, value in data.items()
        }

    # Anything else, return the original form
    return data


# Object Proxies


class ContextProxy(pyblish.api.Context):
    """Context Proxy

    Given a JSON-representation of a Context, emulate its interface.

    """

    def create_instance(self, name, **kwargs):
        instance = InstanceProxy(name, parent=self)
        instance.data.update(kwargs)
        return instance

    @classmethod
    def from_json(cls, context):
        self = cls()
        self._id = context["id"]
        self._data = context["data"]
        self[:] = list(InstanceProxy.from_json(i)
                       for i in context["children"])

        # Attach metadata
        self._data["pyblishClientVersion"] = pyblish.api.version

        return self

    def to_json(self):
        return {
            "name": self.name,
            "id": self.id,
            "data": dict(self.data),  # Convert pyblish.plugin._Dict object
            "children": list(self),
        }


class InstanceProxy(pyblish.api.Instance):
    """Instance Proxy

    Given a JSON-representation of an Instance, emulate its interface.

    """

    @classmethod
    def from_json(cls, instance):
        self = cls(instance["name"])
        self._id = instance["id"]
        self._data = instance["data"]
        self[:] = instance["children"]

        return self

    def to_json(self):
        return {
            "name": self.name,
            "id": self.id,
            "data": dict(self.data),
            "children": list(self),
        }


class PluginProxy(object):
    """Plug-in Proxy

    Given a JSON-representation of an Plug-in, emulate its interface.

    """

    @classmethod
    def from_json(cls, plugin):
        """Build PluginProxy object from incoming dictionary

        Emulate a plug-in by providing access to attributes
        in the same way they are accessed using the remote object.
        This allows for it to be used by members of :mod:`pyblish.logic`.

        """

        process = None
        repair = None

        name = plugin["name"] + "Proxy"
        cls = type(name, (cls,), plugin)

        # Emulate function
        for name in ("process", "repair"):
            args = ", ".join(plugin["process"]["args"])
            func = "def {name}({args}): pass".format(name=name,
                                                     args=args)
            exec(func)

        cls.process = process
        cls.repair = repair

        cls.__orig__ = plugin

        return cls

    @classmethod
    def to_json(cls):
        return cls.__orig__.copy()
