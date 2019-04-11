from .version import (
    version,
    version_info,
    __version__
)


def show(parent=None, targets=None, modal=None, foster=None, comment=None, auto_publish_at_first_run=False):
    from . import host

    if foster is not None:
        print("Foster Mode has been deprecated.")

    if targets is None:
        targets = []
    return host.show(parent, targets, modal, comment, auto_publish_at_first_run)


_state = {}

__all__ = [
    "__version__",
    "version",
    "show",
    "version_info",
]
