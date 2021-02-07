import json as _json_internal
import string
import random


def safe_loads(data):
    try:
        return _json_internal.loads(data)
    except: # noqa
        return {}


def safe_int(it, default):
    try:
        return int(it)
    except ValueError:
        return default


def random_str(length=12, lower=True, upper=True, digits=True):
    items = []
    if lower:
        items += string.ascii_lowercase
    if upper:
        items += string.ascii_uppercase
    if digits:
        items += '0123456789'

    # TODO use cryptographic randomness
    result_str = ''.join(random.choice(items) for i in range(length))

    return result_str


def dumps(data, indent=None):
    return _json_internal.dumps(
        data,
        indent=indent,
        default=str,
    )


def loads(data):
    return _json_internal.loads(data)


def update_allowed_fields(result, allowed_to_update, new_fields):
    for field in allowed_to_update:
        if field in new_fields:
            result[field] = new_fields[field]
    return result


def update_model(model, allowed_to_update, new_fields):
    for field in allowed_to_update:
        if field in new_fields:
            setattr(model, field, new_fields[field])
    return model


def filter_dict_from(d, item):
    return {a: b for a, b in d.items() if b != item}
