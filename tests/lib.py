import sys
import threading

import pyblish.api

import pyblish_rpc.server
import pyblish_rpc.service

from PyQt5 import QtCore

app = None
thread = None
server = None
port = 50999

self = sys.modules[__name__]


def _setup():
    if self.app is None:
        self.app = QtCore.QCoreApplication.instance()

    if self.app is None:
        self.app = QtCore.QCoreApplication(sys.argv)

    service = pyblish_rpc.service.RpcService()
    self.server = pyblish_rpc.server._server(self.port, service)

    self.thread = threading.Thread(target=self.server.serve_forever)

    self.thread.daemon = True
    self.thread.start()

    clean()


def _teardown():
    self.server.shutdown()
    self.thread.join(timeout=1)
    assert not thread.isAlive()


def clean():
    pyblish.api.deregister_all_paths()
    pyblish.api.deregister_all_plugins()
    pyblish.api.deregister_all_services()
