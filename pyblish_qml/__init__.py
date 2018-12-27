from .version import (
    version,
    version_info,
    __version__
)


def show(parent=None, targets=None, modal=None, foster=None):
    from . import host

    if foster is not None:
        print("Foster Mode has been deprecated.")

    if targets is None:
        targets = []
    return host.show(parent, targets, modal)


_state = {}

__all__ = [
    "__version__",
    "version",
    "show",
    "version_info",
]
