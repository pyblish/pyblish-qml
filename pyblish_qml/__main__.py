"""Pyblish QML command-line interface"""

import sys
import argparse

from . import app


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--aschild", action="store_true",
                        help="Run as child of another process")

    kwargs = parser.parse_args()

    return app.main(**kwargs.__dict__)


sys.exit(cli())
