import os
import json
import threading

from ..vendor.nose.tools import *
from .. import services
from .. import mocking

# Dependencies
import pyblish_endpoint.server
import pyblish_endpoint.schema

service = services.Service(
    address="http://127.0.0.1",
    port=7000)

os.environ["ENDPOINT_PORT"] = str(service.port)
server = threading.Thread(
    target=pyblish_endpoint.server.start_production_server,
    kwargs={"port": service.port, "service": mocking.MockService})

server.daemon = True
server.start()


def setup():
    global service
    global server

    data = dict()

    def on_error(error):
        data["error"] = error

    assert_true(service.init(on_error=on_error))
    assert_false("error" in data)


@with_setup(setup)
def test_state():
    """Getting state works as expected"""

    state = service.state()

    pyblish_endpoint.schema.validate(state, schema="state")

    names = [p["name"] for p in state["plugins"]]
    assert_true("SelectInstances" in names)


@with_setup(setup)
def test_process_context():
    """Processing context with a single plug-in works"""
    state = service.state()
    assert_true("context" in state)
    assert_equals(state["context"]["children"], [])

    result = service.process_context("SelectInstances")
    pyblish_endpoint.schema.validate(result, schema="result")


@with_setup(setup)
def test_process_context_missing_plugin():
    """Passing a non-existant plug-in to service yields valid result"""

    result = service.process_context("DoesNotExist")
    assert_false(result["success"])
    assert_equals(result["plugin"], "DoesNotExist")
