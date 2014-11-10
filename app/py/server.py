# Standard library
import threading

# Dependencies
import flask
import flask.ext.restful
import requests

# Local library
import rest

app = flask.Flask(__name__)
api = flask.ext.restful.Api(app)

api.add_resource(rest.Instance, "/instance")
api.add_resource(rest.Publish, "/publish")

PORT = 6000


def start(port=None, safe=False):
    """Start server
    Arguments:
        safe (bool): Ensure there is no existing server already running
    """

    if safe:
        stop()

    if port:
        global PORT
        PORT = port

    def run():
        app.run(port=PORT)

    thread = threading.Thread(target=run)
    thread.daemon = True
    thread.start()
    print "Running Flask server @ port %i.." % PORT

    return thread


def stop():
    try:
        requests.get("http://127.0.0.1:%i/shutdown" % PORT)
    except:
        pass


def restart():
    stop()
    start()


def _shutdown_server():
    """Shutdown the currently running server"""
    func = flask.request.environ.get("werkzeug.server.shutdown")
    if func is not None:
        func()


@app.route("/shutdown", methods=["POST"])
def _shutdown():
    """Shutdown server
    Utility endpoint for remotely shutting down server.
    Usage:
        $ curl -X GET http://127.0.0.1:6000/shutdown
    """

    print "Server shutting down..."
    _shutdown_server()
    print "Server stopped"
    return True


if __name__ == '__main__':
    app.run(port=PORT, debug=True)
