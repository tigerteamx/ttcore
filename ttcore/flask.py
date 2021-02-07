from functools import wraps
from pydantic import ValidationError


def _response_maker(status, status_code, msg, kwargs):
    from flask import jsonify
    kwargs['status'] = status

    if msg:
        kwargs['msg'] = msg

    response = jsonify(**kwargs)
    response.status_code = status_code
    return response


def err(msg=None, **kwargs):
    return _response_maker('error', 400, msg, kwargs)


def warn(msg=None, **kwargs):
    return _response_maker('warning', 200, msg, kwargs)


def not_found(msg=None, **kwargs):
    return _response_maker('error', 404, msg, kwargs)


def ok(msg=None, **kwargs):
    return _response_maker('ok', 200, msg, kwargs)


def html_error(msg, status):
    from flask import render_template
    return render_template(
        'error.html',
        msg=msg
    ), status


def expect_form(form):
    def wrapper1(func):
        @wraps(func)
        def wrapper2(*args, **kwargs):
            from flask import request
            from .utils import loads
            try:
                if request.method in ['POST', 'PUT', 'DELETE']:
                    if not request.is_json:
                        return err('Required to send JSON')
                    setattr(request, 'form', form(**request.json))

                if request.method == 'GET':
                    setattr(request, 'form', form(**request.args))

                return func(*args, **kwargs)
            except ValidationError as e:
                return err("Invalid Input", errors=loads(e.json()))

        return wrapper2
    return wrapper1


def user_or_fail2(func):
    """ OBSOLETE """
    @wraps(func)
    def wrapper(*args, **kwargs):
        from flask import request
        if request.user is None:
            return err('Please login to use this functionality')
        return func(*args, **kwargs)
    return wrapper


def init_user_or_fail(app, get_user_or_none):
    """ OBSOLETE """
    @app.before_request
    def get_and_check_site():
        from flask import request
        setattr(request, 'user', get_user_or_none())
