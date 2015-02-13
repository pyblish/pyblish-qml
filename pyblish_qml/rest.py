"""RESTful communication with the outside world"""

from vendor import requests
import threading

ADDRESS = "http://127.0.0.1:{port}{prefix}{endpoint}"
PORT = 6000


def request(verb, endpoint, data=None, prefix="/pyblish/v1", **kwargs):
    endpoint = ADDRESS.format(port=PORT, endpoint=endpoint, prefix=prefix)
    request = getattr(requests, verb.lower())
    response = request(endpoint, data=data, **kwargs)
    return response


def post_state(state):
    response = request("POST", "/state", data={"state": state})
    if response.status_code != 200:
        raise Exception(response.get("message") or "An error occurred")


def post_next(signal):
    def worker():
        response = request("POST", "/next")
        while response.status_code == 200:
            signal.emit(response.json())
            response = request("POST", "/next")
        signal.emit({"finished": True, "message": "Finished"})

    thread = threading.Thread(target=worker)
    thread.daemon = True
    thread.start()
