import logging

import pyblish_endpoint.service
import pyblish_endpoint.mocking

log = logging.getLogger("qml")


class MockService(pyblish_endpoint.mocking.MockService):
    pass
