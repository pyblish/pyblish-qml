import os
import sys
from PyQt5 import QtGui, QtQuick, QtCore
from pyblish_qml import models2


# Example
class Application(QtGui.QGuiApplication):
    def __init__(self):
        super(Application, self).__init__(sys.argv)

        window = QtQuick.QQuickView()
        window.setResizeMode(window.SizeRootObjectToView)

        window.setWidth(200)
        window.setHeight(200)

        model = models2.ResultModel()

        # Add a number of items
        model.add_item(**{"itemType": "instance",
                          "name": "Linus",
                          "color": "brown"})
        model.add_item(**{"itemType": "plugin",
                          "name": "Snork",
                          "color": "lightgray"})
        model.add_item(**{"itemType": "instance",
                          "name": "Belly",
                          "color": "green"})

        import_path = os.path.dirname(__file__)
        import_path = os.path.join(import_path, "qml")

        engine = window.engine()
        engine.addImportPath(import_path)

        context = engine.rootContext()
        context.setContextProperty("objModel", model)

        window.setSource(QtCore.QUrl.fromLocalFile("qml/temp.qml"))

        window.show()

        self.window = window
        self.model = model


if __name__ == '__main__':
    app = Application()
    app.exec_()
