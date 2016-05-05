try:
    import httplib
except ImportError:
    # Python 3
    import http.client as httplib

try:
    from xmlrpclib import Transport, ServerProxy
except ImportError:
    # Python 3
    from xmlrpc.client import Transport, ServerProxy


class TimeoutTransport(Transport):
    """Requests should happen instantly"""
    def __init__(self, timeout=5, *args, **kwargs):
        Transport.__init__(self, *args, **kwargs)
        self.timeout = timeout

    def make_connection(self, host):
        h = HttpWithTimeout(host, timeout=self.timeout)
        return h


class HttpWithTimeout(httplib.HTTP):
    def __init__(self, host="", port=None, strict=None, timeout=5.0):
        self._setup(self._connection_class(
            host,
            port if port != 0 else None,
            strict,
            timeout=timeout)
        )

    def getresponse(self, *args, **kw):
        return self._conn.getresponse(*args, **kw)


def proxy(timeout=5):
    """Return proxy at default location of Pyblish QML"""
    return ServerProxy(
        "http://127.0.0.1:9090",
        allow_none=True)
