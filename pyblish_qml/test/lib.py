import sys
import time

from PyQt5 import QtCore

from .. import rest

# Local library
import data

_app = None
_plugins = list()


def setup():
    global _app

    if _app is None:
        _app = QtCore.QCoreApplication.instance()

    if _app is None:
        _app = QtCore.QCoreApplication(sys.argv)

    rest._Host = rest.Host
    rest.Host = HostMock


def teardown():
    rest.Host = rest._Host


class HostMock(object):
    delay = 0

    def __init__(self, port):
        self.port = port

    def init(self):
        """Initialisation never fails"""

        plugins = list()
        for plugin in _plugins:
            plugin = data.load(type=data.Plugin, name=plugin)
            plugins.append(plugin)

        self._state = {
            "plugins": plugins,
            "context": {
                "data": {},
                "children": list()
            }
        }

        time.sleep(self.delay)
        return True

    def hello(self):
        """Host is always there"""
        return True

    def save(self, changes):
        """Saving never fails"""
        time.sleep(self.delay)
        return True

    def state(self):
        time.sleep(self.delay)
        return self._state

    def process(self, pair):
        print "HostMock.process(%s)" % (pair)
        time.sleep(self.delay)

        plugin = data.load(type=data.Plugin, name=pair["plugin"])
        instance = data.load(
            type=data.Instance,
            name=pair["instance"]) if pair["instance"] else dict()

        order = plugin["data"]["order"]

        error = None
        records = list()

        for item in (plugin, instance):
            if item.get("__fails__", False):
                error = item.get("__exception__")

            for record in item.get("__records__", list()):
                records.append(record)

        if order < 1:  # Selectors
            for inst in plugin["__instances__"]:
                inst = data.load(type=data.Instance, name=inst)
                self._state["context"]["children"].append(inst)

        elif order < 2:  # Validators
            pass

        elif order < 3:  # Extractors
            pass

        elif order < 4:  # Conformers
            pass

        else:  # All else
            pass

        result = {
            "success": True,
            "instance": pair["instance"],
            "plugin": pair["plugin"],
            "duration": self.delay,
            "error": error,
            "records": records
        }

        return result

    def repair(self, pair):
        pair["mode"] = "repair"
        response = self.request("PUT", "/state", data=pair)
        if response.status_code == 200:
            return response.json()["result"]
        else:
            return IOError("There was an error whilst "
                           "repairing: %s" % response)
