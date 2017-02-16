"""JSON Schema utilities

Attributes:
    cache: Cache of previously loaded schemas

Resources:
    http://json-schema.org/
    http://json-schema.org/latest/json-schema-core.html
    http://spacetelescope.github.io/understanding-json-schema/index.html

"""

import os
import json

from ..vendor import six, jsonschema

cache = {}

MODULE_DIR = os.path.dirname(__file__)
SCHEMA_DIR = os.path.join(MODULE_DIR, "schema")


def load_all():
    for schema in os.listdir(SCHEMA_DIR):
        if schema.startswith(("_", ".")):
            continue
        if not schema.endswith(".json"):
            continue
        if not os.path.isfile(os.path.join(SCHEMA_DIR, schema)):
            continue
        with open(os.path.join(SCHEMA_DIR, schema)) as f:
            cache[schema] = json.load(f)


def validate(data, schema):
    if isinstance(schema, six.string_types):
        schema = cache[schema + ".json"]

    resolver = jsonschema.RefResolver(
        "",
        None,
        store=cache,
        cache_remote=True)
    return jsonschema.validate(data, schema, types={"array": (list, tuple)},
                               resolver=resolver)


ValidationError = jsonschema.ValidationError

load_all()

__all__ = ["validate",
           "ValidationError"]
