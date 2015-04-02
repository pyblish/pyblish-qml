from vendor import requests

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
