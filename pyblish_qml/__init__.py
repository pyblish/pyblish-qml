from .version import (
    version,
    version_info,
    __version__
)


def show(parent=None, targets=[], modal=None):
    from . import host
    return host.show(parent, targets, modal)


_state = {}

__all__ = [
    "__version__",
    "version",
    "show",
    "version_info",
]
