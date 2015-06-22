import os
from SimpleXMLRPCServer import SimpleXMLRPCServer

first_port = 6001


class QmlApi(object):
    def __init__(self, app):
        self.app = app
        self.ctrl = CtrlApi(app.controller)

    def show(self, port, settings=None):
        """Show the GUI

        Arguments:
            port (int): Port with which to communicate with client
            settings (optional, dict): Client settings

        """

        self.app.show_signal.emit(port, settings)
        return True

    def hide(self):
        """Hide the GUI"""
        self.app.hide_signal.emit()
        return True

    def quit(self):
        """Ask the GUI to quit"""
        self.app.quit_signal.emit()
        return True

    def kill(self):
        """Forcefully destroy the process, this does not return"""
        os._exit(1)

    def heartbeat(self, port):
        """Tell QML that someone is listening at `port`"""
        self.app.register_heartbeat(port)

    def find_available_port(self):
        """Return the next available port at which a client may listen"""
        available = first_port
        while available in self.app.clients:
            available += 1
        return available


class CtrlApi(object):
    def __init__(self, ctrl):
        self.ctrl = ctrl


def _server(port, service):
    server = SimpleXMLRPCServer(
        ("127.0.0.1", port),
        allow_none=True,
        logRequests=False)

    server.register_introspection_functions()
    server.register_instance(service)

    return server


def _serve(port, service):
    server = _server(port, service)
    print("Listening on %s:%s" % server.server_address)
    return server.serve_forever()
