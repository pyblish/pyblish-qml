import os
import sys
import logging
import inspect
import traceback

from . import schema

import pyblish.lib
import pyblish.plugin

log = logging.getLogger("pyblish")


def extract_traceback(exception):
    try:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        exception.traceback = traceback.extract_tb(exc_traceback)[-1]

    except Exception:
        pass

    finally:
        del(exc_type, exc_value, exc_traceback)


def format_result(result):
    """Serialise Result"""
    instance = None
    error = None

    if result["instance"] is not None:
        instance = format_instance(result["instance"])

    if result["error"] is not None:
        error = format_error(result["error"])

    result = {
        "success": result["success"],
        "plugin": format_plugin(result["plugin"]),
        "instance": instance,
        "error": error,
        "records": format_records(result["records"]),
        "duration": result["duration"]
    }

    if os.getenv("PYBLISH_SAFE"):
        schema.validate(result, "result")

    return result


def format_records(records):
    """Serialise multiple records"""
    formatted = list()
    for record_ in records:
        formatted.append(format_record(record_))
    return formatted


def format_record(record):
    """Serialise LogRecord instance"""

    record = dict(
        (key, getattr(record, key, None))
        for key in (
            "threadName",
            "name",
            "thread",
            "created",
            "process",
            "processName",
            "args",
            "module",
            "filename",
            "levelno",
            "exc_text",
            "pathname",
            "lineno",
            "msg",
            "exc_info",
            "funcName",
            "relativeCreated",
            "levelname",
            "msecs")
    )

    # Humanise output and conform to Exceptions
    record["message"] = str(record.pop("msg"))

    if os.getenv("PYBLISH_SAFE"):
        schema.validate(record, "record")

    return record


def format_error(error):
    """Serialise exception"""
    formatted = {"message": str(error)}

    if hasattr(error, "traceback"):
        fname, line_no, func, exc = error.traceback
        formatted.update({
            "fname": fname,
            "line_number": line_no,
            "func": func,
            "exc": exc
        })

    return formatted


def format_data(data):
    """Serialise instance/context data

    Arguments:
        data (dict): Data to serialise

    Returns:
        data (dict): Serialised data

    """

    # These are the only data members
    # accessible from the client
    return dict((key, data[key]) for key in (

        # Essential data from each instance
        "name",
        "label",
        "family",
        "families",
        "category",
        "publish",
        "comment",

        # Allows an instance to be non-optional (ie, mandatory)
        "optional",

        # Provided by service.py
        "host",
        "port",
        "user",
        "connectTime",
        "pyblishVersion",
        "pyblishRPCVersion",
        "pythonVersion")

        if key in data
    )


def format_instance(instance):
    """Serialise `instance`

    For children to be visualised and modified,
    they must provide an appropriate implementation
    of __str__.

    Data that isn't JSON compatible cannot be
    visualised nor modified.

    Attributes:
        name (str): Name of instance
        niceName (str, optional): Nice name of instance
        family (str): Name of compatible family
        data (dict, optional): Associated data
        publish (bool): Whether or not instance should be published

    Returns:
        Dictionary of JSON-compatible instance

    """

    instance = {
        "name": instance.name,
        "id": instance.id,
        "data": format_data(instance.data),
        "children": list(),
    }

    if os.getenv("PYBLISH_SAFE"):
        schema.validate(instance, "instance")

    return instance


def format_context(context):
    return {
        "name": context.name,
        "id": context.id,
        "data": format_data(context.data),
        "children": list(format_instance(i) for i in context)
    }


def format_targets(targets):
    return ", ".join(targets)


def format_plugins(plugins):
    """Serialise multiple plug-in

    Returns:
        List of JSON-compatible plug-ins

    """

    formatted = []
    for plugin_ in plugins:
        formatted_plugin = format_plugin(plugin_)
        formatted.append(formatted_plugin)

    return formatted


def format_plugin(plugin):
    """Serialise `plugin`

    Attributes:
        name: Name of Python class
        id: Unique identifier
        version: Plug-in version
        category: Optional category
        requires: Plug-in requirements
        order: Plug-in order
        optional: Is the plug-in optional?
        doc: The plug-in documentation
        hasRepair: Can the plug-in perform a repair?
        hasCompatible: Does the plug-in have any compatible instances?
        type: Which baseclass does the plug-in stem from? E.g. Validator
        module: File in which plug-in was defined
        contextEnabled: Does it process the Context?
        instanceEnabled: Does it process Instance(s)?

    """

    type = "Other"

    for order, _type in {pyblish.plugin.CollectorOrder: "Collector",
                         pyblish.plugin.ValidatorOrder: "Validator",
                         pyblish.plugin.ExtractorOrder: "Extractor",
                         pyblish.plugin.IntegratorOrder: "Integrator"}.items():
        if pyblish.lib.inrange(plugin.order, base=order):
            type = _type

    module = plugin.__module__

    if module == "__main__":
        # Support for in-memory plug-ins.
        path = "mem:%s" % plugin.__name__
    else:
        try:
            path = os.path.abspath(sys.modules[module].__file__)
        except Exception:
            path = "unknown"

    has_repair = False

    args = inspect.getargspec(plugin.repair).args
    if "context" in args or "instance" in args:
        has_repair = True

    # Legacy abilities
    if hasattr(plugin, "repair_context") or hasattr(plugin, "repair_instance"):
        has_repair = True

    output = {
        "label": plugin.label,
        "id": plugin.id,
        "version": plugin.version,
        "category": getattr(plugin, "category", None),
        "requires": plugin.requires,
        "order": plugin.order,
        "optional": plugin.optional,
        "hosts": plugin.hosts,
        "families": plugin.families,

        # New in pyblish-base 1.5.2
        "targets": getattr(plugin, "targets", list()),

        "doc": inspect.getdoc(plugin),
        "active": plugin.active,
        "match": plugin.match,

        # Metadata
        "__pre11__": plugin.__pre11__,
        "__contextEnabled__": plugin.__contextEnabled__,
        "__instanceEnabled__": plugin.__instanceEnabled__,

        "path": path,
        "pre11": plugin.__pre11__,
        "contextEnabled": plugin.__contextEnabled__,
        "instanceEnabled": plugin.__instanceEnabled__,
        "name": plugin.__name__,
        "type": type,
        "module": module,
        "hasRepair": has_repair,
        "process": {
            "args": inspect.getargspec(plugin.process).args,
        },
        "repair": {
            "args": inspect.getargspec(plugin.repair).args,
        },

        "actions": [format_action(a) for a in plugin.actions],
    }

    if os.getenv("PYBLISH_SAFE"):
        schema.validate(output, "plugin")

    return output


def format_action(action):
    return {
        "id": action.id,
        "label": action.label or action.__name__,
        "description": action.__doc__,
        "active": action.active,
        "icon": action.icon or "",
        "on": action.on,
        "__type__": action.__type__,
        "__error__": action.__error__,
    }
