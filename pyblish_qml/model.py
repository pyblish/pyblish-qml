"""Model components used in QML"""

from PyQt5 import QtCore


class Item(object):
    def __init__(self, name, **kwargs):
        self.name = name
        for key, value in kwargs.iteritems():
            setattr(self, key, value)


class Model(QtCore.QAbstractListModel):
    _roles = dict()

    def __init__(self, parent=None):
        super(Model, self).__init__(parent)
        self.items = list()

    def addItem(self, item):
        self.beginInsertRows(QtCore.QModelIndex(),
                             self.rowCount(),
                             self.rowCount())
        self.items.append(item)
        self.endInsertRows()

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.items)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        return QtCore.QVariant()

    def roleNames(self):
        return self._roles

    @QtCore.pyqtSlot(int, str, str)
    def setData(self, index, role, value):
        item = self.items[index]
        setattr(item, role, value)

        qindex = self.createIndex(index, 0)
        self.dataChanged.emit(qindex, qindex)

    def itemByName(self, name):
        for item in self.items:
            if item.name == name:
                return item

    def itemIndex(self, item):
        return self.items.index(item)

    def itemIndexByName(self, name):
        item = self.itemByName(name)
        return self.itemIndex(item)

    @property
    def serialized(self):
        serialized = list()
        for item in self.items:
            serialized.append(item.__dict__)
        return serialized


class InstanceModel(Model):

    NameRole = QtCore.Qt.UserRole + 3
    FamilyRole = QtCore.Qt.UserRole + 4
    IsToggledRole = QtCore.Qt.UserRole + 5
    ActiveRole = QtCore.Qt.UserRole + 6
    CurrentProgressRole = QtCore.Qt.UserRole + 7
    IsSelectedRole = QtCore.Qt.UserRole + 8
    IsProcessingRole = QtCore.Qt.UserRole + 9
    IsCompatibleRole = QtCore.Qt.UserRole + 10
    HasErrorRole = QtCore.Qt.UserRole + 11
    HasWarningRole = QtCore.Qt.UserRole + 12
    HasMessageRole = QtCore.Qt.UserRole + 13
    OptionalRole = QtCore.Qt.UserRole + 14
    ErrorsRole = QtCore.Qt.UserRole + 15
    WarningsRole = QtCore.Qt.UserRole + 16
    MessagesRole = QtCore.Qt.UserRole + 17

    _roles = {
        NameRole: "name",
        FamilyRole: "family",
        IsToggledRole: "isToggled",
        ActiveRole: "active",
        CurrentProgressRole: "currentProgress",
        IsSelectedRole: "isSelected",
        IsProcessingRole: "isProcessing",
        IsCompatibleRole: "isCompatible",
        HasErrorRole: "hasError",
        HasWarningRole: "hasWarning",
        HasMessageRole: "hasMessage",
        OptionalRole: "optional",
        ErrorsRole: "errors",
        WarningsRole: "warnings",
        MessagesRole: "messages"
    }

    def data(self, index, role=QtCore.Qt.DisplayRole):
        try:
            item = self.items[index.row()]
        except IndexError:
            return QtCore.QVariant()

        if role in self._roles:
            return getattr(item, self._roles[role])

        return QtCore.QVariant()


class PluginModel(InstanceModel):
    OrderRole = QtCore.Qt.UserRole + 30
    FamiliesRole = QtCore.Qt.UserRole + 31
    TypeRole = QtCore.Qt.UserRole + 32

    _roles = InstanceModel._roles
    _roles[OrderRole] = "order"
    _roles[FamiliesRole] = "families"
    # _roles[TypeRole] = "type"


if __name__ == '__main__':
    model = Model()
    model.addItem(Item("test"))
    print model.children()
