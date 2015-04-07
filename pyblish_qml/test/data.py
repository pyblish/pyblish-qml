import os
import json


Plugin = "plugin"
Instance = "instance"

_cache = {}
module_dir = os.path.dirname(__file__)


def load(type, name):
    print "data.load(%s, %s)" % (type, name)
    fname = "%s_%s.json" % (type, name)

    if fname not in _cache:
        path = os.path.join(module_dir, "data", fname)
        with open(path, "r") as f:
            _cache[fname] = json.load(f)

    data = _cache[fname]
    data["name"] = name
    return data


def dump(type, name, indent=4):
    return json.dumps(load(type, name), indent=indent, sort_keys=True)
