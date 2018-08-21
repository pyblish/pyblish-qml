from .version import (
    version,
    version_info,
    __version__
)


def show(parent=None, targets=None, modal=None, foster=None):
    from . import host

    if targets is None:
        targets = []
    return host.show(parent, targets, modal, foster)


_state = {}

__all__ = [
    "__version__",
    "version",
    "show",
    "version_info",
]
