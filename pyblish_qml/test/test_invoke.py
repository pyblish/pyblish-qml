import sys
import time
from PyQt5 import QtCore, QtWidgets


class invoke(QtCore.QThread):
    done = QtCore.pyqtSignal(QtCore.QVariant, arguments=["result"])

    def __init__(self, target, callback=None):
        super(invoke, self).__init__()

        self.target = target

        if callback:
            self.done.connect(callback)

        self.start()

    def run(self, *args, **kwargs):
        result = self.target(*args, **kwargs)
        self.done.emit(result)


class Window(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)

        self.t = invoke(self.expensive_function,
                        self.on_expensive_function)

        print "After invoke, before expensive_function"

    def expensive_function(self):
        time.sleep(1)
        return 5

    def on_expensive_function(self, result):
        print "on_expensive_function() returned: %s" % result
        print "isRunning: %s" % self.t.isRunning()
        print "isFinished: %s" % self.t.isFinished()


app = QtWidgets.QApplication(sys.argv)

window = Window()
window.show()

sys.exit(app.exec_())
