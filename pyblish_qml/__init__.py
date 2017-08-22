from .version import (
    version,
    version_info,
    __version__
)


def show(parent=None, targets=[]):
    from . import host
    return host.show(parent, targets)


_state = {}

__all__ = [
    "__version__",
    "version",
    "show",
    "version_info",
]
