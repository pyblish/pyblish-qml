import sys
import threading

import pyblish_rpc.server
import pyblish_rpc.service

from PyQt5 import QtCore

self = sys.modules[__name__]

app = None
thread = None
server = None
port = 50998

self.app = QtCore.QCoreApplication.instance() or QtCore.QCoreApplication(sys.argv)

service = pyblish_rpc.service.RpcService()
self.server = pyblish_rpc.server._server(self.port, service)

self.thread = threading.Thread(target=self.server.serve_forever)

self.thread.daemon = True
self.thread.start()
