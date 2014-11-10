
# Standard library
import json

# Dependencies
import flask.ext.restful


def loads(data):
    """Load JSON as string instead of unicode objects
    Arguments:
        data (str): String of JSON data
    """

    return convert(json.loads(data))


def convert(input):
    """Cast input to string
    Arguments:
        input (object): Dict, list or unicode object to be converted
    """

    if isinstance(input, dict):
        return dict((convert(k), convert(v)) for k, v in input.iteritems())
    elif isinstance(input, list):
        return [convert(e) for e in input]
    elif isinstance(input, unicode):
        return input.encode("utf-8")
    else:
        return input


class Instance(flask.ext.restful.Resource):
    def get(self):
        return [
            {
                "instance": "Richard01",
                "family": "napoleon.model"
            },
            {
                "instance": "Richard02",
                "family": "napoleon.rig"
            },
            {
                "instance": "Napoleon01",
                "family": "napoleon.rig"
            },
            {
                "instance": "Peter01",
                "family": "napoleon.rig"
            },
            {
                "instance": "Zion12",
                "family": "napoleon.animation"
            },
        ]


class Publish(flask.ext.restful.Resource):
    def post(self):
        data_str = flask.request.stream.read()
        data_json = loads(data_str)

        print data_json

        return {
            "message": "success",
            "status": 200
        }

# class Api(flask.ext.restful.Resource):
#     def post(self):
#         data_str = flask.request.stream.read()
#         data_json = loads(data_str)

#         command = data_json.get("command") or None
#         if command is None:
#             return {"message": "Must provide a command"}

#         try:
#             module, attribute = command.split(".")
#         except ValueError:
#             module, attribute = "cmds", command

#         args = data_json.get("args") or list()
#         kwargs = data_json.get("kwargs") or dict()

#         try:
#             _mod = getattr(wrapper, module)
#             getattr(_mod, attribute)(*args, **kwargs)
#             return {"message": True}
#         except Exception as e:
#             return {"message": str(e)}
