from .vendor.six.moves import xmlrpc_client as xmlrpclib


def proxy(timeout=5):
    """Return proxy at default location of Pyblish QML"""
    return xmlrpclib.ServerProxy(
        "http://127.0.0.1:9090",
        allow_none=True)
