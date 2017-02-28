from .version import (
    version,
    version_info,
    __version__
)


def show(parent=None):
    from . import host
    return host.show(parent)


_state = {}

__all__ = [
    "__version__",
    "version",
    "show",
    "version_info",
]
