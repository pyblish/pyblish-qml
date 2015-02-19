import time
import logging

import pyblish.api
import pyblish_endpoint.service


log = logging.getLogger("qml")


class MockService(pyblish_endpoint.service.EndpointService):
    """Service for testing

    Attributes:
        SLEEP_DURATION: Fake processing delay, in milliseconds
        NUM_INSTANCES: Fake amount of available instances (max: 2)
        PERFORMANCE: Enum of fake performance. Available values are
            SLOW, MODERATE, FAST, NATIVE

    """

    SLEEP_DURATION = 0
    NUM_INSTANCES = 3

    SLOW = 1 << 0
    MODERATE = 1 << 1
    FAST = 1 << 2
    NATIVE = 1 << 3
    PERFORMANCE = NATIVE

    def init(self):
        self.plugins = []
        for plugin, superclass in (
                ["ExtractAsMa", pyblish.api.Extractor],
                ["ConformAsset", pyblish.api.Conformer]):
            obj = type(plugin, (superclass,), {})

            obj.families = ["napoleon.animation.cache"]

            if plugin == "ConformAsset":
                obj.families = ["napoleon.asset.rig"]

            obj.hosts = ["python", "maya"]
            self.plugins.append(obj)

        fake_instances = ["Peter01", "Richard05", "Steven11"]
        context = pyblish.api.Context()
        for name in fake_instances[:self.NUM_INSTANCES]:
            instance = context.create_instance(name=name)

            instance._data = {
                "identifier": "napoleon.instance",
                "minWidth": 800,
                "assetSource": "/server/assets/Peter",
                "destination": "/server/published/assets",
            }

            instance.set_data("publish", True)

            if name == "Peter01":
                instance.set_data("publish", False)
                instance.set_data("family", "napoleon.asset.rig")
            else:
                instance.set_data("family", "napoleon.animation.cache")

            for node in ["node1", "node2", "node3"]:
                instance.append(node)

        self.plugins.append(ValidateFailureMock)
        self.plugins.append(ValidateNamespace)
        self.plugins = self.sort_plugins(self.plugins)

        self.context = context
        self.processor = None

    def next(self):
        result = super(MockService, self).next()
        self.sleep()
        return result

    def sleep(self):
        if self.SLEEP_DURATION:
            log.info("Pretending it takes %s seconds "
                     "to complete.." % self.SLEEP_DURATION)

            performance = self.SLEEP_DURATION
            if self.PERFORMANCE & self.SLOW:
                performance += 2

            if self.PERFORMANCE & self.MODERATE:
                performance += 1

            if self.PERFORMANCE & self.FAST:
                performance += 0.1

            if self.PERFORMANCE & self.NATIVE:
                performance = 0

            increment_sleep = performance / 3.0

            time.sleep(increment_sleep)
            log.info("Running first pass..")

            time.sleep(increment_sleep)
            log.info("Almost done..")

            time.sleep(increment_sleep)
            log.info("Completed successfully!")


#
# Mock classes
#

@pyblish.api.log
class ValidateNamespace(pyblish.api.Validator):
    """Ensure name-spaces are in order."""

    families = ["napoleon.animation.cache"]
    hosts = ["*"]
    version = (0, 0, 1)
    category = "names"

    def process_instance(self, instance):
        self.log.info("Validating namespace..")
        self.log.info("Completed validating namespace!")


@pyblish.api.log
class ValidateFailureMock(pyblish.api.Validator):
    """A plug-in that always fails."""

    families = ["*"]
    hosts = ["*"]
    version = (0, 0, 1)
    optional = True
    category = "mocks"

    def process_instance(self, instance):
        raise ValueError("Instance failed")
