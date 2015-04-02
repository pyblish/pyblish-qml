"""Model components used in QML"""

from PyQt5 import QtCore


defaults = {
    "name": "default",
    "isSelected": False,
    "isProcessing": False,
    "isToggled": True,
    "optional": True,
    "hasError": False,
    "succeeded": False,
    "currentProgress": 0,
    "errors": list(),
    "records": list()
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
}

instance_defaults = {
    "family": "default",
    "niceName": "default"
}


class Item(object):
    default_data = {}

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__str__()

    def __init__(self, name, data):
        for key, value in defaults.iteritems():
            if data.get(key) is not None:
                value = data[key]
            setattr(self, key, value)

        self.name = name
        self.data = data


class InstanceItem(Item):
    def __init__(self, *args, **kwargs):
        super(InstanceItem, self).__init__(*args, **kwargs)

        for key, value in instance_defaults.iteritems():
            if self.data.get(key) is not None:
                value = self.data[key]
            setattr(self, key, value)


class PluginItem(Item):
    def __init__(self, *args, **kwargs):
        super(PluginItem, self).__init__(*args, **kwargs)

        for key, value in plugin_defaults.iteritems():
            if self.data.get(key) is not None:
                value = self.data[key]
            setattr(self, key, value)

        doc = self.data["doc"]
        if doc and len(doc) > 30:
            self.data["doc"] = doc[:30] + "..."


class Model(QtCore.QAbstractListModel):
    roles = dict()
    names = dict()

    data_changed = QtCore.pyqtSignal(object, str, object, object,
                                     arguments=["name", "key", "old", "new"])

    def pairs(self):
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

                if not any(x in plugin.data["families"] for x in (
                        instance.data["family"], "*")):
                    continue

                yield plugin, instance

    def has_failed_validator(self):
        for validator in self.plugins:
            if validator.order != 1:
                continue
            if validator.hasError:
                return True
        return False

    def errors(self):
        """Parse and return current errors"""
        errors = dict()
        for plugin in self.plugins:
            for error in plugin.errors:
                if plugin.name not in errors:
                    errors[plugin] = list()
                errors[plugin].append(error)
        return errors

    def __new__(cls, *args, **kwargs):
        obj = super(Model, cls).__new__(cls, *args, **kwargs)

        index = 0
        for key in (defaults.keys() +
                    instance_defaults.keys() +
                    plugin_defaults.keys()):
            role = QtCore.Qt.UserRole + index
            obj.roles[role] = key
            index += 1

        obj.names = dict((v, k) for k, v in obj.roles.iteritems())
        obj.roles[999] = "itemType"

        return obj

    def __init__(self, parent=None):
        super(Model, self).__init__(parent)
        self.items = list()
        self.item_dict = dict()
        self.instances = list()
        self.plugins = list()

    def addItem(self, item):
        self.beginInsertRows(QtCore.QModelIndex(),
                             self.rowCount(),
                             self.rowCount())

        self.items.append(item)

        # Performance buffers
        self.item_dict[item.name] = item
        if isinstance(item, PluginItem):
            self.plugins.append(item)
        elif isinstance(item, InstanceItem):
            self.instances.append(item)

        self.endInsertRows()

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.items)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if isinstance(index, QtCore.QModelIndex):
            index = index.row()

        try:
            item = self.items[index]
        except IndexError:
            return QtCore.QVariant()

        if role == 999:
            return type(item).__name__

        if role in self.roles:
            return getattr(item, self.roles[role], None)

        return QtCore.QVariant()

    def roleNames(self):
        return self.roles

    def setData(self, index, key, value):
        if isinstance(index, QtCore.QModelIndex):
            index = index.row()

        item = self.items[index]

        try:
            old = getattr(item, key)
        except AttributeError:
            print "%s did not exist"
            return

        setattr(item, key, value)

        if key in item.data:
            item.data[key] = value

        qindex = self.createIndex(index, 0)
        self.dataChanged.emit(qindex, qindex)
        self.data_changed.emit(item, key, old, value)

    def itemFromName(self, name):
        return self.item_dict.get(name)

    def itemFromIndex(self, index):
        return self.items[index]

    def itemIndexFromName(self, name):
        item = self.itemFromName(name)
        return self.itemIndexFromItem(item)

    def itemIndexFromItem(self, item):
        return self.items.index(item)

    @property
    def serialized(self):
        serialized = list()
        for item in self.items:
            serialized.append(item.data)
        return serialized

    def reset(self):
        self.beginResetModel()
        self.items[:] = []

        # Clear caches too
        self.item_dict.clear()
        self.instances[:] = []
        self.plugins[:] = []

        self.endResetModel()


class TerminalModel(QtCore.QAbstractListModel):
    roles = [
        "type",
        "filter",
        "message",

        # LogRecord
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
        "msecs",

        # Exception
        "fname",
        "line_number",
        "func",
        "exc",

        # Context
        "port",
        "host",
        "user",
        "connectTime",
        "pythonVersion",
        "pyblishVersion",
        "endpointVersion",

        # Plugin
        "doc",
        "instance",
        "plugin"
    ]

    added = QtCore.pyqtSignal()

    def __new__(cls, *args, **kwargs):
        obj = super(TerminalModel, cls).__new__(cls, *args, **kwargs)

        roles = dict()
        for index in range(len(obj.roles)):
            role = obj.roles[index]
            roles[QtCore.Qt.UserRole + index] = role

        obj.roles = roles
        obj.names = dict((v, k) for k, v in roles.iteritems())

        return obj

    def __init__(self, parent=None):
        super(TerminalModel, self).__init__(parent)
        self.items = []

    def addItem(self, item):
        self.beginInsertRows(QtCore.QModelIndex(),
                             self.rowCount(),
                             self.rowCount())

        self.items.append(item)
        self.endInsertRows()
        self.added.emit()

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.items)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        try:
            item = self.items[index.row()]
        except IndexError:
            return QtCore.QVariant()

        if role in self.roles:
            return item.get(self.roles[role], QtCore.QVariant())

        return QtCore.QVariant()

    def roleNames(self):
        return self.roles

    def reset(self):
        self.beginResetModel()
        self.items[:] = []
        self.endResetModel()


class ProxyModel(QtCore.QSortFilterProxyModel):
    """A QSortFilterProxyModel with custom exclusion

    Example:
        >>> # Exclude any item whose role 123 equals "Abc"
        >>> model = ProxyModel()
        >>> model.addExclusion(role=123, value="Abc")

    """

    @property
    def names(self):
        return self.sourceModel().names

    def __init__(self, source, parent=None):
        super(ProxyModel, self).__init__(parent)
        self.setSourceModel(source)

        self.excludes = dict()
        self.includes = dict()

    def addExclusion(self, role, value):
        """Exclude item if `role` equals `value`

        Attributes:
            role (int): Qt role to compare `value` to
            value (object): Value to exclude

        """

        if not isinstance(role, int):
            role = self.names[role]

        self.excludes[role] = value
        self.invalidate()

    def removeExclusion(self, role):
        """Remove exclusion rule

        TODO(marcus): Should we allow for multiple excluded
            *values* for each role? For example, if a role
            matches *any* or *all* of the excluded values
            it could get excluded. How should the logic look
            for something like that?

        """

        if not isinstance(role, int):
            role = self.names[role]

        self.excludes.pop(role, None)
        self.invalidate()

    def addInclusion(self, role, value):
        """Include item if `role` equals `value`

        Attributes:
            role (int): Qt role to compare `value` to
            value (object): Value to exclude

        """

        self.includes[role] = value
        self.invalidate()

    def filterAcceptsRow(self, source_row, source_parent):
        """Exclude items in `self.excludes`"""
        model = self.sourceModel()
        index = model.index(source_row, 0, QtCore.QModelIndex())

        for role, value in self.includes.iteritems():
            data = model.data(index, role)
            if data != value:
                return False

        for role, value in self.excludes.iteritems():
            data = model.data(index, role)
            if data == value:
                return False

        return super(ProxyModel, self).filterAcceptsRow(
            source_row, source_parent)


class InstanceProxy(ProxyModel):
    def __init__(self, *args, **kwargs):
        super(InstanceProxy, self).__init__(*args, **kwargs)
        self.addInclusion(999, "InstanceItem")


class PluginProxy(ProxyModel):
    def __init__(self, *args, **kwargs):
        super(PluginProxy, self).__init__(*args, **kwargs)
        self.addInclusion(999, "PluginItem")
        self.addExclusion("type", "Selector")
        self.addExclusion("hasCompatible", False)


class TerminalProxy(ProxyModel):
    def __init__(self, *args, **kwargs):
        super(TerminalProxy, self).__init__(*args, **kwargs)
        self.setFilterRole(self.names["filter"])  # msg
        self.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.addExclusion("levelname", "DEBUG")
