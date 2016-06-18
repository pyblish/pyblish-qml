"""Pyblish QML command-line interface"""

import sys
import argparse

from . import app


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--validate", action="store_true")

    kwargs = parser.parse_args()

    return app.main(debug=kwargs.debug,
                    validate=kwargs.validate)


sys.exit(cli())
