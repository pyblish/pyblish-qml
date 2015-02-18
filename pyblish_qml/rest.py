from vendor import requests

ADDRESS = "http://127.0.0.1:{port}/pyblish/v1{endpoint}"
PORT = 6000


def request(verb, endpoint, data=None, **kwargs):
    endpoint = ADDRESS.format(port=PORT,
                              endpoint=endpoint)
    request = getattr(requests, verb.lower())
    response = request(endpoint, data=data, **kwargs)
    return response
