import sys

# User-editable settings

ContextLabel = ContextLabelDefault = "Context"
WindowTitle = WindowTitleDefault = "Pyblish"
WindowSize = (430, 600)
WindowPosition = (100, 100)
HeartbeatInterval = 60
HiddenSections = ["Collect"]

# Implementation details below.

self = sys.modules[__name__]
self._callbacks = dict()


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
        "HiddenSections"
    })
