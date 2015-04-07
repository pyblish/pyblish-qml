"""Pyblish QML command-line interface

Arguments:
    port (int): Port at which to communicate with Pyblish Endpoint
    pid (int, optional): Process ID of parent process
    preload (bool, optional): Whether or not to pre-load the GUI

"""

import sys
import argparse

import app


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="Python")  # deprecated
    parser.add_argument("--port", type=int, default=6000)
    parser.add_argument("--pid", type=int, default=None)
    parser.add_argument("--preload", action="store_true")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--validate", action="store_true")

    kwargs = parser.parse_args()
    port = kwargs.port
    pid = kwargs.pid
    preload = kwargs.preload
    debug = kwargs.debug
    validate = kwargs.validate

    return app.main(port=port,
                    pid=pid,
                    debug=debug or port == 6000,
                    preload=preload,
                    validate=validate)


sys.exit(cli())
