import json

import util
util.register_vendor_libraries()

# Vendor libraries
import requests

ConnectionError = requests.ConnectionError


def request(address, port, verb, endpoint, **kwargs):
    """Make a request to Endpoint

    Attributes:
        verb (str): GET, PUT, POST or DELETE request
        endpoint (str): Tail of endpoint; e.g. /client
        data (dict, optional): Data used for POST or PUT requests

    """

    endpoint = "%s:%s/pyblish/v1%s" % (address, port, endpoint)
    request = getattr(requests, verb.lower())
    response = request(endpoint, **kwargs)

    return response


class Host(object):
    def __init__(self, port):
        self.port = port

    def init(self):
        response = self.request("POST", "/state")

        if response.status_code != 200:
            message = response.json().get(
                "message", "An error occured whilst "
                "initialising host: %s" % response)

            return IOError(message)

        return True

    def hello(self):
        try:
            self.request("GET", "/hello", timeout=0.1)
        except ConnectionError:
            return False
        return True

    def save(self, changes):
        response = self.request("POST", "/state", data={
            "changes": json.dumps(changes, indent=4)})

        if response.status_code != 200:
            message = response.json().get("message") or "An error occurred"
            return IOError(message)

        return True

    def state(self):
        response = self.request("GET", "/state")
        if response.status_code != 200:
            message = response.json().get(
                "message", "Could not get state: "
                "%s" % response)

            return IOError(message)

        state = response.json()["state"]

        return state

    def process(self, pair):
        response = self.request("PUT", "/state", data=pair)
        if response.status_code == 200:
            return response.json()["result"]
        else:
            plugin = pair.get("plugin")
            instance = pair.get("instance")
            message = response.json().get(
                "message", "Could not get state: "
                "%s" % response)
            return IOError("There was an error whilst "
                           "publishing (%s, %s): %s" % (
                            plugin, instance, message))

    def repair(self, pair):
        pair["mode"] = "repair"
        response = self.request("PUT", "/state", data=pair)
        if response.status_code == 200:
            return response.json()["result"]
        else:
            plugin = pair.get("plugin")
            instance = pair.get("instance")
            message = response.json().get(
                "message", "Could not get state: "
                "%s" % response)
            return IOError("There was an error whilst "
                           "repairing (%s, %s): %s" % (
                            plugin, instance, message))

    def rpc(self, function, **kwargs):
        response = self.request(
            "POST", "/rpc/%s" % function,
            data={"kwargs": json.dumps(kwargs, indent=4)})
        if response.status_code == 200:
            return response.json()["result"]
        else:
            return IOError("RPC command failed: %s" % response)

    def request(self, *args, **kwargs):
        return request("http://127.0.0.1",
                       self.port, *args, **kwargs)
