import os
import sys
import json
import threading
import subprocess

import pyblish.api
import pyblish.lib
import pyblish.logic

from . import service as service_
from ..vendor.six.moves import (
    xmlrpc_server as xmlrpclib,
    socketserver
)


self = sys.modules[__name__]
self.current_server_thread = None
self.current_server = None
self.dispatch_wrapper = None


def default_wrapper(func, *args, **kwargs):
    return func(*args, **kwargs)


class RpcServer(socketserver.ThreadingMixIn, xmlrpclib.SimpleXMLRPCServer):
    """An RPC server

    This server relies on a port and socket for interprocess communication.

    Support multiple requests simultaneously. This is important,
    as we will still want to emit heartbeats during a potentially
    long process.

    About paths, the API is accessible from both the root /pyblish and
    suffixed with an exact version, such as /pyblish/v1. The root always
    references the latest version.

    """

    def __init__(self, path, *args, **kwargs):
        class VerifyingRequestHandler(xmlrpclib.SimpleXMLRPCRequestHandler):
            rpc_paths = ("/pyblish", path)

            def parse_request(this):
                if xmlrpclib.SimpleXMLRPCRequestHandler.parse_request(this):
                    if self.authenticate(this.headers):
                        return True
                else:
                    this.send_error(401, "Authentication failed")

                return False

        xmlrpclib.SimpleXMLRPCServer.__init__(
            self,
            requestHandler=VerifyingRequestHandler,
            *args,
            **kwargs)

    def authenticate(self, headers):
        """TODO(marcus): Implement basic authentication"""
        # basic, _, encoded = headers.get("Authorization").partition(" ")
        # assert basic == "Basic", "Only basic authentication supported"
        # username, _, password = base64.b64decode(encoded).partition(":")
        # assert username == "marcus"
        # assert password == "pass"
        return True

    def _dispatch(self, *args):
        wrapper = sys.modules[__name__].dispatch_wrapper or default_wrapper
        return wrapper(xmlrpclib.SimpleXMLRPCServer._dispatch,
                       self, *args)


class PopenServer(object):
    """A subprocess server

    This server relies on stdout and stdin for interprocess communication.

    """

    def __init__(self, service, python, pyqt5):
        super(PopenServer, self).__init__()
        self.service = service

        CREATE_NO_WINDOW = 0x08000000

        self.popen = subprocess.Popen(
            [python, "-u", "-m", "pyblish_qml", "--popen"],
            env=dict(os.environ, **{
                "PYTHONHOME": os.path.split(python)[0],
                "PYTHONPATH": os.pathsep.join([
                    os.getenv("PYTHONPATH", ""),
                    pyqt5,
                ])
            }),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,

            # This is only relevant on Windows, but does
            # no harm on other OSs.
            creationflags=CREATE_NO_WINDOW
        )

        thread = threading.Thread(target=self._listen)
        thread.daemon = True
        thread.start()

    def stop(self):
        return self.popen.kill()

    def wait(self):
        return self.popen.wait()

    def _listen(self):
        for line in iter(self.popen.stdout.readline, b""):
            try:
                response = json.loads(line)
            except Exception:
                sys.stdout.write(line)
            else:
                if response["header"] == "pyblish-qml:popen.request":
                    payload = response["payload"]
                    args = payload["args"]

                    # wrapper = sys.modules[__name__].dispatch_wrapper \
                    #     or default_wrapper
                    func = getattr(self.service, payload["name"])
                    result = func(*args)

                    data = json.dumps({
                        "header": "pyblish-qml:popen.response",
                        "payload": result
                    })

                    self.popen.stdin.write(data + "\n")
                    self.popen.stdin.flush()


def kill():
    """Shutdown a running server"""
    print("Shutting down..")
    return self.current_server.shutdown()


def _server(port, service):
    server = RpcServer(
        "/pyblish",
        ("127.0.0.1", port),
        allow_none=True,
        logRequests=False)

    server.register_function(kill)
    server.register_introspection_functions()
    server.register_instance(service, allow_dotted_names=True)

    self.current_server = server

    return server


def _serve(port, service=None):
    if service is None:
        service = service_.Service()

    server = _server(port, service)
    print("Listening on %s:%s" % server.server_address)
    server.serve_forever()


def start_production_server(port, service=None):
    """Run server with optimisations

    Arguments:
        port (int): Port at which to listen for incoming requests
        service (Service): Service responding to requests

    """

    return _serve(port, service)


def start_async_production_server(port, service=None):
    """Start a threaded version of production server

    Returns Thread object.

    """

    def worker():
        start_production_server(port, service)

    thread = threading.Thread(target=worker)
    thread.daemon = True
    thread.start()

    self.current_server_thread = thread

    return thread


def start_debug_server(port=6000, delay=0.5):
    """Start debug server

    This server uses a mocked up service to fake the actual
    behaviour and data of a generic host; incuding faked time
    it takes to perform a task.

    Arguments:
        port (int, optional): Port at which to listen for requests.
            Defaults to 6000.
        delay (float, optional): Simulate time taken to process requests.
            Defaults to 0.5 seconds.

    """

    pyblish.lib.setup_log("pyblish")
    service = service_.MockService()
    return _serve(port, service)


if __name__ == '__main__':
    PopenServer(
        service=service_.MockService(),
        python="C:/python27/python.exe",
        pyqt5="C:/modules/python-qt5"
    ).wait()
