"""Model components used in QML"""

from PyQt5 import QtCore


class Item(object):
    defaults = {
        "publish": True,
    }

    defaults_gui = {
        "name": "default",
        "objName": "default",
        "family": "default",
        "families": "default",
        "isSelected": False,
        "currentProgress": 0,
        "isProcessing": False,
        "hasCompatible": False,
        "hasError": False,
        "hasWarning": False,
        "hasMessage": False,
        "optional": True,
        "succeeded": False,
        "errors": list(),
        "warnings": list(),
        "messages": list(),
        "doc": None,
        "order": None,
        "families": list(),
        "type": None,
    }

    def __str__(self):
        return self.data["name"]

    def __repr__(self):
        return self.__str__()

    def __init__(self, **kwargs):
        data = self.defaults.copy()
        data.update(self.defaults_gui)
        data.update(kwargs)
        self.data = data


class Model(QtCore.QAbstractListModel):
    _roles = dict()

    data_changed = QtCore.pyqtSignal(
        str, str, object, object,
        arguments=["name", "key", "old", "new"])

    def __new__(cls, *args, **kwargs):
        instance = super(Model, cls).__new__(cls, *args, **kwargs)

        index = 0
        for key in Item.defaults.keys() + Item.defaults_gui.keys():
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
        self.item_dict[item.data.get("name")] = item

        self.endInsertRows()

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.items)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        try:
            item = self.items[index.row()]
        except IndexError:
            return QtCore.QVariant()

        if role in self._roles:
            return item.data.get(self._roles[role])

        return QtCore.QVariant()

    def roleNames(self):
        return self._roles

    @QtCore.pyqtSlot(int, str, str)
    def setData(self, index, role, value):
        item = self.items[index]
        old = item.data.get(role)

        item.data[role] = value

        qindex = self.createIndex(index, 0)
        self.dataChanged.emit(qindex, qindex)
        self.data_changed.emit(item.data.get("name"), role, old, value)

    def itemFromName(self, name):
        for item in self.items:
            if item.data.get("name") == name:
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
            while item.data["family"] not in families:
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
