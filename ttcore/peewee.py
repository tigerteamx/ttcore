

def get_or_fail(model):
    """ OBSOLETE """
    from flask import abort
    from ttcore.flask import err
    instance = model.first()
    if instance is None:
        return abort(err('Could not find model', model=model.model.__name__))
    return instance


def _get_or_response(model, response):
    from flask import abort
    instance = model.first()
    if instance is None:
        return abort(response(
            'Could not find model', model=model.model.__name__))
    return instance


def get_or_500(model):
    from ttcore.flask import err
    return _get_or_response(model, err)


def get_or_404(model):
    from ttcore.flask import not_found
    return _get_or_response(model, not_found)
