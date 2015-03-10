"""Mockup of host"""

import os
import sys
import threading
import subprocess

from PyQt5 import QtWidgets

import pyblish_qml.app
import pyblish_qml.mocking

import pyblish_endpoint.client
import pyblish_endpoint.server
import pyblish_endpoint.service


if __name__ == '__main__':
    port = 6001
    pid = os.getpid()
    data = dict(count=0)

    thread = threading.Thread(
        target=pyblish_endpoint.server.start_production_server,
        kwargs={"port": port, "service": pyblish_qml.mocking.MockService})

    thread.daemon = True
    thread.start()

    kwargs = dict(args=["python", "-m", "pyblish_qml",
                        "--port", str(port),
                        "--pid", str(pid),
                        "--preload"])

    kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE

    gui = subprocess.Popen(**kwargs)

    app = QtWidgets.QApplication(sys.argv)
    window = QtWidgets.QWidget()
    button_show = QtWidgets.QPushButton("Show")

    def on_clicked(message):
        print "Pressed: %i" % data["count"]
        data["count"] += 1
        pyblish_endpoint.client.request(message)

    button_show.clicked.connect(lambda: on_clicked("show"))

    button_other = QtWidgets.QPushButton("Other")
    button_other.clicked.connect(lambda: on_clicked("other"))

    layout = QtWidgets.QHBoxLayout(window)
    layout.addWidget(button_show)
    layout.addWidget(button_other)

    window.setFixedSize(250, 50)
    window.show()

    print "Running Test with pid: %s" % pid
    print "Running GUI with pid: %s" % gui.pid

    sys.exit(app.exec_())
