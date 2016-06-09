try:
    from xmlrpclib import Transport, ServerProxy
except ImportError:
    # Python 3
    from xmlrpc.client import Transport, ServerProxy


def proxy(timeout=5):
    """Return proxy at default location of Pyblish QML"""
    return ServerProxy(
        "http://127.0.0.1:9090",
        allow_none=True)
