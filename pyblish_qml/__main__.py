"""Pyblish QML command-line interface"""

import sys
import argparse

from . import app


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true",
                        help="Illustrate features of the GUI")
    parser.add_argument("--debug", action="store_true",
                        help="Development mode")
    parser.add_argument("--validate", action="store_true",
                        help="Check system prior to launching")

    kwargs = parser.parse_args()

    return app.main(debug=kwargs.debug or kwargs.demo,
                    validate=kwargs.validate)


sys.exit(cli())
