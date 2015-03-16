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
        self.reset()

        context = pyblish.api.Context()
        plugins = []

        for plugin in PLUGINS:
            if issubclass(plugin, pyblish.api.Selector):
                for inst, err in plugin().process(context):
                    pass

            plugin.families = ["napoleon.animation.cache"]
            if plugin == "ConformAsset":
                plugin.families = ["napoleon.asset.rig"]

            plugin.hosts = ["python"]
            plugins.append(plugin)

        pyblish.api.sort_plugins(plugins)

        self.context = context
        self.plugins = plugins

    def advance(self):
        result = super(MockService, self).advance()
        self.__sleep()
        return result

    def __sleep(self):
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


ExtractAsMa = type("ExtractAsMa", (pyblish.api.Extractor,), {})
ConformAsset = type("ConformAsset", (pyblish.api.Conformer,), {})


@pyblish.api.log
class SelectInstances(pyblish.api.Selector):
    hosts = ["*"]

    def process_context(self, context):
        for name in INSTANCES:
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


@pyblish.api.log
class ValidateNamespace(pyblish.api.Validator):
    """Ensure name-spaces are in order.

    And this is a long description. Lorem ipsum and what not. La la la, long.

    """

    families = ["napoleon.animation.cache"]
    hosts = ["*"]
    version = (0, 0, 1)
    category = "names"

    def process_instance(self, instance):
        self.log.info("Validating namespace..")
        self.log.info("Completed validating namespace!")

    def process_context(self, context):
        self.log.info("Processed context..")


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

    def process_context(self, context):
        self.log.info("Processed context..")


INSTANCES = [
    "Peter01",
    "Richard05",
    "Steven11",
    "Piraya12",
    "Marcus"
]

PLUGINS = [
    SelectInstances,
    ExtractAsMa,
    ConformAsset,
    ValidateFailureMock,
    ValidateNamespace
]
