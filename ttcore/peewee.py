

def get_or_fail(model):
    from flask import abort
    from ttcore.flask import err
    instance = model.first()
    if instance is None:
        return abort(err('Could not find model', model=model.model.__name__))
    return instance
