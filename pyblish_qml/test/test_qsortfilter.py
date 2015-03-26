import sys
from PyQt5 import QtCore, QtWidgets


class ProxyModel(QtCore.QSortFilterProxyModel):
    def __init__(self, parent=None):
        super(ProxyModel, self).__init__(parent)

        self.excludes = dict()

    def addExclusion(self, role, value):
        """Exclude item if `role` equals `value`

        Attributes:
            role (int): Qt role to compare `value` to
            value (object): Value to exclude

        """

        self.excludes[role] = value
        self.invalidate()

    def filterAcceptsRow(self, source_row, source_parent):
        """Exclude items in `self.excludes`"""
        model = self.sourceModel()
        index = model.index(source_row, 0, QtCore.QModelIndex())

        for role, value in self.excludes.iteritems():
            data = model.data(index, role)
            if data == value:
                return False

        return super(ProxyModel, self).filterAcceptsRow(
            source_row, source_parent)


class Model(QtCore.QAbstractListModel):
    def __init__(self, parent=None):
        super(Model, self).__init__(parent)
        self.items = [
            {
                "name": "Marcus",
                "age": 28
            },
            {
                "name": "Lukas",
                "age": 55
            },
            {
                "name": "Albert",
                "age": 55
            },
            {
                "name": "Richard",
                "age": 65
            },
            {
                "name": "Mans",
                "age": 28
            },
            {
                "name": "Tito",
                "age": 111
            }
        ]

    def addItem(self, item):
        self.beginInsertRows(QtCore.QModelIndex(),
                             self.rowCount(),
                             self.rowCount())

        self.items.append(item)
        self.endInsertRows()

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.items)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        try:
            item = self.items[index.row()]
        except IndexError:
            return QtCore.QVariant()

        roles = self.roleNames()
        if role in roles:
            return item.get(roles[role])

        return QtCore.QVariant()

    def roleNames(self):
        return {
            QtCore.Qt.DisplayRole: "name",
            258: "age"
        }


app = QtWidgets.QApplication(sys.argv)

window = QtWidgets.QWidget()

model = Model()
proxy = ProxyModel()
proxy.setSourceModel(model)

view = QtWidgets.QListView()
view.setModel(proxy)


def add_exclude():
    data = lineedit.text()

    name, value = data.split(":")

    roles = dict((v, k) for k, v in model.roleNames().items())

    try:
        role = roles[name]
    except:
        print "Available keys: name, age"
        return

    try:
        value = int(value)
    except:
        pass

    proxy.addExclusion(role, value)
    lineedit.clear()
    lineedit.setFocus()


lineedit = QtWidgets.QLineEdit()
lineedit.returnPressed.connect(add_exclude)
lineedit.setPlaceholderText("key:value to exclude..")

layout = QtWidgets.QVBoxLayout(window)
layout.addWidget(view)
layout.addWidget(lineedit)

proxy.addExclusion(258, 28)

source_item = model.items[0]
source_row = model.items.index(source_item)
source_index = model.index(source_row, 0, QtCore.QModelIndex())
proxy.mapFromSource(source_index).row()
proxy.sort(QtCore.Qt.DisplayRole, QtCore.Qt.AscendingOrder)
# Do you exist in the proxy?
print proxy.mapFromSource(source_index).row()

window.show()

sys.exit(app.exec_())
