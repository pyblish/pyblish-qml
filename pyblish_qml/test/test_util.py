import sys
import time

from PyQt5 import QtCore

from ..vendor.nose.tools import *
from .. import util

app = None


def setup():
    if QtCore.QCoreApplication.instance():
        return

    global app
    app = QtCore.QCoreApplication(sys.argv)


@with_setup(setup)
def test_invoke():
    """util.invoke works as expected"""

    mutable = dict()

    def expensive_function():
        time.sleep(0.1)
        return 5

    def on_expensive_function(result):
        mutable["result"] = result
        app.quit()

    qthread = util.invoke(expensive_function,
                          callback=on_expensive_function)

    app.exec_()

    assert_true(qthread.wait(200))
    assert_equals(mutable["result"], 5)
