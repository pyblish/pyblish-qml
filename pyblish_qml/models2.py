from PyQt5 import QtCore

import util

defaults = {
    "name": "default",
    "isSelected": False,
    "isProcessing": False,
    "isToggled": True,
    "optional": True,
    "hasError": False,
    "succeeded": False,
    "processed": False,
    "currentProgress": 0
}

plugin_defaults = {
    "optional": False,
    "doc": None,
    "order": None,
    "hasRepair": False,
    "hasCompatible": False,
    "families": list(),
    "hosts": list(),
    "type": "unknown",
    "canProcessContext": False,
    "canProcessInstance": False,
    "canRepairInstance": False,
    "canRepairContext": False,
    "compatibleInstances": list(),
}

instance_defaults = {
    "family": "default",
    "niceName": "default",
    "compatiblePlugins": list(),
}


class PropertyType(QtCore.pyqtWrapperType):
    """Metaclass for converting class attributes into pyqtProperties

    Usage:
        >>> class AbstractClass(QtCore.QObject):
        ...     __metaclass__ = PropertyType

    """

    prefix = "__pyqtproperty__"

    def __new__(cls, name, bases, attrs):
        for key, value in attrs.copy().items():
            if key.startswith("__"):
                continue

            notify = QtCore.pyqtSignal()

            def set_data(key, value):
                def set_data(self, value):
                    setattr(self, cls.prefix + key, value)
                    getattr(self, key + "Changed").emit()
                return set_data

            attrs[key + "Changed"] = notify
            attrs[key] = QtCore.pyqtProperty(
                type(value),
                fget=lambda self, k=key: getattr(self, cls.prefix + k, None),
                fset=set_data(key, value),
                notify=notify)

        return super(PropertyType, cls).__new__(cls, name, bases, attrs)


class AbstractItem(QtCore.QObject):
    __metaclass__ = PropertyType


def Item(**kwargs):
    """Factory for QAbstractListModel items

    Any class attributes are converted into pyqtProperties
    and must be declared with its type as value.

    Usage:
        >>> item = Item(name="default name",
        ...             age=5,
        ...             alive=True)
        >>> assert item.name == "default name"
        >>> assert item.age == 5
        >>> assert item.alive == True
        >>>
        >>> # Jsonifyable content
        >>> assert item.json == {
        ...     "name": "default name",
        ...     "age": 5,
        ...     "alive": True
        ...     }, item.json

    """

    cls = type("Item", (AbstractItem,), kwargs.copy())

    self = cls()
    self.json = kwargs  # Store as json

    for key, value in kwargs.items():
        if hasattr(self, key):
            key = PropertyType.prefix + key
        setattr(self, key, value)

    return self


class AbstractModel(QtCore.QAbstractListModel):
    def __init__(self, parent=None):
        super(AbstractModel, self).__init__(parent)
        self.items = util.ItemList(key="name")

    def add_item(self, **item):
        self.beginInsertRows(QtCore.QModelIndex(),
                             self.rowCount(),
                             self.rowCount())

        item = Item(**item)
        self.items.append(item)
        self.endInsertRows()

        return item

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.items)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.UserRole:
            try:
                return self.items[index.row()]
            except IndexError:
                pass

        return QtCore.QVariant()

    def roleNames(self):
        return {
            QtCore.Qt.UserRole: "item"
        }

    def reset(self):
        self.beginResetModel()
        self.items[:] = []
        self.endResetModel()


class ItemModel(AbstractModel):
    def __init__(self, *args, **kwargs):
        super(ItemModel, self).__init__(*args, **kwargs)
        self.plugins = util.ItemList(key="name")
        self.instances = util.ItemList(key="name")

    def add_item(self, **item):
        item = super(ItemModel, self).add_item(**item)
        type = item.itemType

        if type == "plugin":
            self.plugins.append(item)

        elif type == "instance":
            self.instances.append(item)

        else:
            raise TypeError("item not instance nore plug-in")

        return item

    def update_with_state(self, state):
        self.reset()

        plugins = state.get("plugins", list())
        context = state.get("context", dict(children=list()))

        for plugin in plugins:
            properties = defaults.copy()
            properties.update(plugin_defaults)
            properties.update(plugin["data"])
            properties["name"] = plugin["name"]
            properties["itemType"] = "plugin"

            if properties["order"] < 1:
                properties["isToggled"] = False

            if properties.get("doc"):
                properties["doc"] = util.format_text(properties.get("doc"))

            self.add_item(**properties)

        for instance in context["children"]:
            properties = defaults.copy()
            properties.update(instance_defaults)
            properties.update(instance.get("data", {}))
            properties["name"] = instance["name"]
            properties["itemType"] = "instance"

            if properties.get("publish") is False:
                properties["isToggled"] = False

            self.add_item(**properties)

    def update_current(self, pair):
        """Update the currently processing pair

        Arguments:
            pair (dict): {"instance": <str>, "plugin": <str>}

        """

        for item in self.items:
            item.isProcessing = False

        for type in ("instance", "plugin"):
            name = pair[type]
            item = self.items.get(name)

            if not item:
                continue

            item.isProcessing = True
            item.currentProgress = 1

    def update_with_result(self, result):
        """Update item-model with result from host

        State is sent from host after processing had taken place
        and represents the events that took place; including
        log messages and completion status.

        Arguments:
            result (dict): Dictionary following the Result schema

        """

        for item in self.items:
            item.isProcessing = False

        for type in ("instance", "plugin"):
            name = result[type]
            item = self.items.get(name)

            if not item:
                assert type == "instance"
                continue

            item.isProcessing = True
            item.currentProgress = 1
            item.processed = True

            if result.get("error"):
                item.hasError = True

            else:
                item.succeeded = True

    def iterator(self):
        """Default iterator

        Yields items to be processed based on their
        current state.

        Yields:
            tuple: (plugin, instance)

        """

        for plugin in self.plugins:
            if not plugin.isToggled:
                continue

            if not plugin.hasCompatible:
                continue

            if plugin.canProcessContext:
                yield plugin, None

            if not plugin.canProcessInstance:
                continue

            for instance in self.instances:
                if not instance.isToggled:
                    continue

                if instance.name not in plugin.compatibleInstances:
                    continue

                yield plugin, instance

    def has_failed_validator(self):
        for validator in self.plugins:
            if validator.order != 1:
                continue
            if validator.hasError:
                return True
        return False

    def reset_status(self):
        """Reset progress bars"""
        for item in self.items:
            item.isProcessing = False
            item.currentProgress = 0

    def update_compatibility(self):
        for plugin in self.plugins:
            has_compatible = False

            for instance in self.instances:
                if not instance.isToggled:
                    continue

                if instance.name in plugin.compatibleInstances:
                    has_compatible = True
                    break

            print "%s.hasCompatible: %s" % (plugin.name, has_compatible)
            plugin.hasCompatible = has_compatible

    def reset(self):
        self.instances[:] = []
        self.plugins[:] = []
        super(ItemModel, self).reset()


result_defaults = {
    "type": "",
    "filter": "",
    "message": "",

    # Temporary metadata: "", until treemodel
    "instance": "",
    "plugin": "",

    # LogRecord
    "threadName": "",
    "name": "",
    "thread": "",
    "created": "",
    "process": "",
    "processName": "",
    "args": "",
    "module": "",
    "filename": "",
    "levelno": 0,
    "levelname": "",
    "exc_text": "",
    "pathname": "",
    "lineno": 0,
    "msg": "",
    "exc_info": "",
    "funcName": "",
    "relativeCreated": "",
    "msecs": 0.0,

    # Exception
    "fname": "",
    "line_number": 0,
    "func": "",
    "exc": "",

    # Context
    "port": 0,
    "host": "",
    "user": "",
    "connectTime": "",
    "pythonVersion": "",
    "pyblishVersion": "",
    "endpointVersion": "",

    # Plugin
    "doc": "",
    "instance": "",
    "plugin": ""
}


class ResultModel(AbstractModel):

    added = QtCore.pyqtSignal()

    def add_item(self, **item):
        try:
            return super(ResultModel, self).add_item(**item)
        finally:
            self.added.emit()

    def update_with_state(self, state):
        self.reset()

        data = state["context"]["data"]

        properties = result_defaults.copy()
        properties.update(data)
        properties.update({
            "type": "context",
            "name": "Pyblish",
            "filter": "Pyblish"
        })

        self.add_item(**properties)

    def update_with_result(self, result):
        parsed = self.parse_result(result)

        error = parsed.get("error")
        plugin = parsed.get("plugin")
        instance = parsed.get("instance")
        records = parsed.get("records")

        if getattr(self, "_last_plugin", None) != plugin:
            self._last_plugin = plugin
            self.add_item(**plugin)

        self.add_item(**instance)

        for record in records:
            self.add_item(**record)

        if error is not None:
            self.add_item(**error)

    def parse_result(self, result):
        plugin_msg = {
            "type": "plugin",
            "message": result["plugin"],
            "filter": result["plugin"],
            "doc": result["doc"],

            "plugin": result["plugin"],
            "instance": result["instance"]
        }

        instance_msg = {
            "type": "instance",
            "message": result["instance"],
            "filter": result["instance"],
            "duration": result["duration"],

            "plugin": result["plugin"],
            "instance": result["instance"]
        }

        record_msgs = list()

        for record in result["records"]:
            record["type"] = "record"
            record["filter"] = record["message"]
            record["message"] = util.format_text(str(record["message"]))

            record["plugin"] = result["plugin"]
            record["instance"] = result["instance"]

            record_msgs.append(record)

        error_msg = {
            "type": "error",
            "message": "No error",
            "filter": "",

            "plugin": result["plugin"],
            "instance": result["instance"]
        }

        error_msg = None

        if result["error"] is not None:
            error = result["error"]
            error["type"] = "error"
            error["message"] = util.format_text(error["message"])
            error["filter"] = error["message"]

            error["plugin"] = result["plugin"]
            error["instance"] = result["instance"]

            error_msg = error

        return {
            "plugin": plugin_msg,
            "instance": instance_msg,
            "records": record_msgs,
            "error": error_msg,
        }


class ProxyModel(QtCore.QSortFilterProxyModel):
    """A QSortFilterProxyModel with custom exclude and include rules

    Role may be either an integer or string, and each
    role may include multiple values.

    Example:
        >>> # Exclude any item whose role 123 equals "Abc"
        >>> model = ProxyModel(None)
        >>> model.add_exclusion(role=123, value="Abc")

        >>> # Exclude multiple values
        >>> model.add_exclusion(role="name", value="Pontus")
        >>> model.add_exclusion(role="name", value="Richard")

        >>> # Exclude amongst includes
        >>> model.add_inclusion(role="type", "PluginItem")
        >>> model.add_exclusion(role="name", "Richard")

    """

    def __init__(self, source, parent=None):
        super(ProxyModel, self).__init__(parent)
        self.setSourceModel(source)

        self.excludes = dict()
        self.includes = dict()

    @QtCore.pyqtSlot(str, str)
    def add_exclusion(self, role, value):
        """Exclude item if `role` equals `value`

        Attributes:
            role (int, string): Qt role or name to compare `value` to
            value (object): Value to exclude

        """

        self._add_rule(self.excludes, role, value)

    @QtCore.pyqtSlot(str, str)
    def remove_exclusion(self, role, value=None):
        """Remove exclusion rule

        Arguments:
            role (int, string): Qt role or name to remove
            value (object, optional): Value to remove. If none
                is supplied, the entire role will be removed.

        """

        self._remove_rule(self.excludes, role, value)

    def set_exclusion(self, rules):
        """Set excludes

        Replaces existing excludes with those in `rules`

        Arguments:
            rules (list): Tuples of (role, value)

        """

        self._set_rules(self.excludes, rules)

    @QtCore.pyqtSlot()
    def clear_exclusion(self):
        self._clear_group(self.excludes)

    @QtCore.pyqtSlot(str, str)
    def add_inclusion(self, role, value):
        """Include item if `role` equals `value`

        Attributes:
            role (int): Qt role to compare `value` to
            value (object): Value to exclude

        """

        self._add_rule(self.includes, role, value)

    @QtCore.pyqtSlot(str, str)
    def remove_inclusion(self, role, value=None):
        """Remove exclusion rule"""
        self._remove_rule(self.includes, role, value)

    def set_inclusion(self, rules):
        self._set_rules(self.includes, rules)

    @QtCore.pyqtSlot()
    def clear_inclusion(self):
        self._clear_group(self.includes)

    def _add_rule(self, group, role, value):
        """Implementation detail"""
        if role not in group:
            group[role] = list()

        group[role].append(value)

        self.invalidate()

    def _remove_rule(self, group, role, value=None):
        """Implementation detail"""
        if role not in group:
            return

        if value is None:
            group.pop(role, None)
        else:
            group[role].remove(value)

        self.invalidate()

    def _set_rules(self, group, rules):
        """Implementation detail"""
        group.clear()

        for rule in rules:
            self._add_rule(group, *rule)

        self.invalidate()

    def _clear_group(self, group):
        group.clear()

        self.invalidate()

    # Overridden methods

    def filterAcceptsRow(self, source_row, source_parent):
        """Exclude items in `self.excludes`"""
        model = self.sourceModel()
        item = model.items[source_row]

        for role, values in self.includes.items():
            data = getattr(item, role, None)
            if data not in values:
                return False

        for role, values in self.excludes.items():
            data = getattr(item, role, None)
            if role == "hasCompatible":
                print "%s.%s = %s in %s" % (item.name, role, data, values)
            if data in values:
                return False

        return super(ProxyModel, self).filterAcceptsRow(
            source_row, source_parent)


class InstanceProxy(ProxyModel):
    def __init__(self, *args, **kwargs):
        super(InstanceProxy, self).__init__(*args, **kwargs)
        self.add_inclusion("itemType", "instance")


class PluginProxy(ProxyModel):
    def __init__(self, *args, **kwargs):
        super(PluginProxy, self).__init__(*args, **kwargs)
        self.add_inclusion("itemType", "plugin")
        self.add_exclusion("type", "Selector")
        self.add_exclusion("hasCompatible", False)


class ResultProxy(ProxyModel):
    def __init__(self, *args, **kwargs):
        super(ResultProxy, self).__init__(*args, **kwargs)
        # self.setFilterRole("item")
        # self.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        # self.add_exclusion("levelname", "DEBUG")


class RecordProxy(ProxyModel):
    def __init__(self, *args, **kwargs):
        super(RecordProxy, self).__init__(*args, **kwargs)
        self.add_inclusion("type", "record")

    def filterAcceptsRow(self, source_row, source_parent):
        return super(RecordProxy, self).filterAcceptsRow(
            source_row, source_parent)


class ErrorProxy(ProxyModel):
    def __init__(self, *args, **kwargs):
        super(ErrorProxy, self).__init__(*args, **kwargs)
        self.add_inclusion("type", "error")


class GadgetProxy(ProxyModel):
    def __init__(self, *args, **kwargs):
        super(GadgetProxy, self).__init__(*args, **kwargs)

