# import time
# import json

# from vendor import requests


# class Service(object):
#     """The receiving end of an Endpoint Service"""
#     def __init__(self, address, port):
#         if address == "localhost":
#             address = "http://127.0.0.1"

#         self.address = address
#         self.port = port

#     def init(self, on_error=None):
#         """Compute current state

#         Arguments:
#             on_error(error) (callable, optional): Function called upon error.

#         Error codes:
#             1: Retrying
#             2: Server unresponsive

#         """

#         if not on_error:
#             def on_error(error):
#                 pass

#         def request():
#             return self.request("POST", "/state")

#         response = request()
#         for attempt in range(2):
#             if response.status_code == 200:
#                 break

#             on_error({
#                 "code": 1,
#                 "message": "Failed to post state; retrying.."
#             })

#             time.sleep(0.2)
#             response = request()

#         if response.status_code != 200:
#             on_error({
#                 "code": 2,
#                 "message": ("Could not post state; "
#                             "is the server running @ %s?"
#                             "Message: %s" % (self.port, response.text))
#             })

#             return False

#         return True

#     def save(self, changes, on_error=None):
#         if not on_error:
#             def on_error(error):
#                 pass

#         serialised_changes = json.dumps(changes, indent=4)

#         response = self.request("POST", "/state",
#                                 data={"changes": serialised_changes})

#         if response.status_code != 200:
#             message = response.json().get("message") or "An error occurred"
#             on_error(message)
#             return False

#         return True

#     def state(self, on_error=None):
#         """Get current state

#         Arguments:
#             on_error(error) (callable, optional): Function called upon error.

#         """

#         if not on_error:
#             def on_error(error):
#                 pass

#         response = self.request("GET", "/state")

#         if response.status_code != 200:
#             on_error({
#                 "code": 1,
#                 "message": response.json()["message"]
#             })

#             return None

#         state = response.json()["state"]

#         return state

#     def validate():
#         """Process all validators"""

#     def process(self,
#                 plugin,
#                 instance=None,
#                 repair=False,
#                 on_processing=None,
#                 on_error=None):

#         """Process `plugin`

#         Arguments:
#             plugin (str): Name of plug-in to process
#             on_processing(pair) (callable, optional): Processing callback
#             on_error(result) (callable, optional): Error callback

#         """

#         if not on_processing:
#             def on_processing(pair):
#                 return None

#         if not on_error:
#             def on_error(error):
#                 return None

#         mode = "repair" if repair else "process"
#         response = self.request("PUT", "/state", data={
#             "plugin": plugin,
#             "instance": instance,
#             "mode": mode
#         })

#         if response.status_code != 200:
#             traceback = response.json().get("message")

#             on_error({
#                 "type": "message",
#                 "message": ("Server responded with code %s "
#                             "during selection with %s "
#                             "(see traceback)" % (
#                                 response.status_code,
#                                 plugin)),
#                 "traceback": traceback
#             })

#             return None

#         else:
#             result = response.json()["result"]
#             return result

#     def process_instance(self,
#                          plugin,
#                          instance,
#                          on_processing=None,
#                          on_error=None):

#         return self.process(plugin,
#                             instance,
#                             on_processing=on_processing,
#                             on_error=on_error)

#     def process_context(self,
#                         plugin,
#                         on_processing=None,
#                         on_error=None):

#         return self.process(plugin,
#                             instance=None,
#                             on_processing=on_processing,
#                             on_error=on_error)

#     def repair_instance(self,
#                         plugin,
#                         instance,
#                         on_processing=None,
#                         on_error=None):

#         return self.process(plugin,
#                             instance,
#                             repair=True,
#                             on_processing=on_processing,
#                             on_error=on_error)

#     def repair_context(self,
#                        plugin,
#                        on_processing=None,
#                        on_error=None):

#         return self.process(plugin,
#                             instance=None,
#                             repair=True,
#                             on_processing=on_processing,
#                             on_error=on_error)

#     def request(self, verb, endpoint, data=None, **kwargs):
#         """Make a request to Endpoint

#         Attributes:
#             verb (str): GET, PUT, POST or DELETE request
#             endpoint (str): Tail of endpoint; e.g. /client
#             data (dict, optional): Data used for POST or PUT requests

#         """

#         endpoint = "%s:%s/pyblish/v1%s" % (self.address, self.port, endpoint)
#         request = getattr(requests, verb.lower())
#         response = request(endpoint, data=data, **kwargs)

#         return response
