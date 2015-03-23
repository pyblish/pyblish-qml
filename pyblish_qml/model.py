"""Model components used in QML"""

from PyQt5 import QtCore


defaults = {
    "name": "default",
    "isSelected": False,
    "isProcessing": False,
    "isToggled": True,
    "optional": True,
    "hasError": False,
    "hasWarning": False,
    "hasMessage": False,
    "succeeded": False,
    "currentProgress": 0,
    "errors": list(),
    "warnings": list(),
    "messages": list(),
}

plugin_defaults = {
    "optional": False,
    "doc": None,
    "hasRepair": False,
    "hasCompatible": False,
    "families": [],
    "hosts": [],
    "type": "unknown",
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
    _roles = dict()

    data_changed = QtCore.pyqtSignal(
        str, str, object, object,
        arguments=["name", "key", "old", "new"])

    def __new__(cls, *args, **kwargs):
        instance = super(Model, cls).__new__(cls, *args, **kwargs)

        index = 0
        for key in (defaults.keys() +
                    instance_defaults.keys() +
                    plugin_defaults.keys()):
            role = QtCore.Qt.UserRole + index
            instance._roles[role] = key
            index += 1

        return instance

    def __init__(self, parent=None):
        super(Model, self).__init__(parent)
        self.items = list()
        self.item_dict = dict()

    def addItem(self, item):
        self.beginInsertRows(QtCore.QModelIndex(),
                             self.rowCount(),
                             self.rowCount())

        self.items.append(item)
        self.item_dict[item.name] = item

        self.endInsertRows()

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.items)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        try:
            item = self.items[index.row()]
        except IndexError:
            return QtCore.QVariant()

        if role in self._roles:
            return getattr(item, self._roles[role])

        return QtCore.QVariant()

    def roleNames(self):
        return self._roles

    def setData(self, index, key, value):
        item = self.items[index]

        try:
            old = getattr(item, key)
        except AttributeError:
            print "%s did not exist"
            return

        setattr(item, key, value)

        qindex = self.createIndex(index, 0)
        self.dataChanged.emit(qindex, qindex)
        self.data_changed.emit(item.name, key, old, value)

    def itemFromName(self, name):
        for item in self.items:
            if item.name == name:
                return item
        raise KeyError("%s not in dict" % name)

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
        self.endResetModel()


class InstanceModel(Model):
    def next_instance(self, index, families):
        try:
            item = self.items[index + 1]
            while item.data.get("family") not in families:
                index += 1
                item = self.items[index]
        except IndexError:
            return None

        return item


class PluginModel(Model):
    def next_plugin(self, index):
        try:
            item = self.items[index + 1]
        except IndexError:
            return None

        return item


if __name__ == '__main__':
    model = InstanceModel()
    model.addItem(Item(name="test"))
    print model.children()
    print model.items
