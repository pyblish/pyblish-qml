"""Pyblish QML command-line interface"""

import sys
import socket
import argparse

from . import app, host


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true",
                        help="Illustrate features of the GUI")
    parser.add_argument("--debug", action="store_true",
                        help="Development mode")
    parser.add_argument("--validate", action="store_true",
                        help="Check system prior to launching")
    parser.add_argument("--kill", action="store_true",
                        help="Kill running QML client")
    kwargs = parser.parse_args()

    # If a QML is already running, re-use this.
    proxy = host.proxy(timeout=5)

    try:
        proxy.ping()

    except (socket.timeout, socket.error):
        return app.main(debug=kwargs.debug or kwargs.demo,
                        validate=kwargs.validate)

    else:
        if kwargs.kill:
            proxy.kill()
            print("Successfully killed client.")


sys.exit(cli())
