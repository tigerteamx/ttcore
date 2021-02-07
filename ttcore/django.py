from django.http import JsonResponse


def jsonify(**kwargs):
    return JsonResponse(dict(**kwargs))


def _response_maker(status, status_code, msg, kwargs):
    kwargs['status'] = status

    if msg:
        kwargs['msg'] = msg

    return JsonResponse(dict(**kwargs), status=status_code)


def err(msg=None, **kwargs):
    return _response_maker('error', 400, msg, kwargs)


def notfound(msg=None, **kwargs):
    return _response_maker('notfound', 404, msg, kwargs)


def warn(msg=None, **kwargs):
    return _response_maker('warning', 200, msg, kwargs)


def ok(msg=None, **kwargs):
    return _response_maker('ok', 200, msg, kwargs)
