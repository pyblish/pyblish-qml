"""Pyblish QML GUI interface

This makes the Pyblish QML package into an executable.

"""

import os
import subprocess
import argparse
import pyblish_qml

CREATE_NO_WINDOW = 0x08000000
PACKAGE_DIR = os.path.dirname(pyblish_qml.__file__)
GUI_PATH = os.path.join(PACKAGE_DIR, "qml", "app.qml")


def parse_args():
    parser = argparse.ArgumentParser(description='Launch GUI')
    parser.add_argument('--qmlscene',
                        type=str,
                        help='Absolute path to qmlscene')
    parser.add_argument('--console',
                        default=False,
                        action="store_true",
                        help='Display console window')

    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()

    kwargs = {}
    if args.console is False:
        kwargs["creationflags"] = CREATE_NO_WINDOW

    creationflags = CREATE_NO_WINDOW if args.console else 0
    proc = subprocess.call([args.qmlscene or "qmlscene", GUI_PATH], **kwargs)
