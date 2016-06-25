import sys

# User-editable settings

ContextLabel = "Context"
WindowTitle = "Pyblish"
WindowSize = (430, 600)
WindowPosition = (100, 100)
HeartbeatInterval = 60

# Implementation details below.

self = sys.modules[__name__]
self._callbacks = dict()
self._current_gui_port = 0
self._current_host_port = 0
self._port_changed_callbacks = list()


def from_dict(settings):
    """Apply settings from dictionary

    Arguments:
        settings (dict): Settings in the form of a dictionary

    """

    assert isinstance(settings, dict), "`settings` must be of type dict"
    for key, value in settings.items():
        setattr(self, key, value)


def to_dict():
    """Return dictionary of settings"""
    return dict((k, getattr(self, k)) for k in {
        "ContextLabel",
        "WindowTitle",
        "WindowSize",
        "WindowPosition",
        "HeartbeatInterval",
    })


def current_host_port():
    """Return port through which QML is currently communicating"""
    return self._current_host_port


def set_current_host_port(port):
    """Set the port with which to communicate"""
    self._current_host_port = port
    for func in self._port_changed_callbacks:
        func(port)


def register_port_changed_callback(func):
    """When the current port changes, trigger the supplied callable

    Arguments:
        func (callable): Callable to run upon a new client registering
            interest in displaying the GUI.

    """

    self._port_changed_callbacks.append(func)
