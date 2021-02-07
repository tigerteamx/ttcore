def regex_options(options):
    from pydantic import constr
    return constr(regex=r'^({})$'.format('|'.join(options)))
