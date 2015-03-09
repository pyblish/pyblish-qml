import json

ADDRESS = "http://127.0.0.1:{port}/pyblish/v1{endpoint}"
PORT = 6000
MOCK = None


def request(verb, endpoint, data=None, **kwargs):
    from vendor import requests
    endpoint = ADDRESS.format(port=PORT, endpoint=endpoint)

    request = getattr(MOCK or requests, verb.lower())
    response = request(endpoint, data=data, **kwargs)

    if not hasattr(response, "json"):
        response.json = lambda: json.loads(response.data)

    return response
