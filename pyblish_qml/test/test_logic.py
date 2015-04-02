# from PyQt5 import QtCore, QtGui

from .. import app


def test_publish_is_detoggled():
    """Instances with `publish` set to False default to detoggled"""
    pass


def test_reset():
    """Reset clears and repopulates models"""
    ctrl = app.Controller()

    ctrl.exec_()
    # assert False
