import json

from django.core.serializers.json import DjangoJSONEncoder


def dumps(data):
    return json.dumps(
        data,
        cls=DjangoJSONEncoder,
    )


def loads(data):
    return json.loads(data)


def lenient_loads(data, default):
    try:
        return loads(data)
    except: # noqa
        return default
