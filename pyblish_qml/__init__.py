import sys
from .version import *

_port = 0
_callbacks = list()
self = sys.modules[__name__]


def current_port():
    return self._port


def set_current_port(port):
    self._port = port
    for func in _callbacks:
        func(port)


def register_client_changed_callback(func):
    _callbacks.append(func)
