from zipfile import ZipFile
import tempfile
from uuid import uuid4
from functools import wraps
from inspect import signature
from dataclasses import dataclass
from datetime import datetime
from traceback import format_exc
import inspect
import time
import os
import shutil


import peewee
from .bottle_origin import request, post, get, hook, response, HTTPResponse, default_app, route, SimpleTemplate


from .utils import mkdir, rmdir, read, is_ip4, dumps


@dataclass
class Context:
    path: str


_docs = []


def _get_doc_params(params):
    doc_params = []
    print("Function parameters:")
    for name, param in params.items():
        param_type = (
            param.annotation.__name__
            if param.annotation != param.empty
            else "Unknown"
        )

        if param_type == "Context":
            continue

        required = param.default == param.empty
        default = param.default if param.default != param.empty else "N/A"
        print(f"- {name}: {param_type} (required={required}, default={default})")
        doc_params.append(dict(
            name=name,
            param_type=param_type,
            required=required,
            default=default,
        ))

    return doc_params


def _auth(roles):
    """
    Check request permissions against the roles
    """
    perms = getattr(request, "perms", [])

    if "admin" in perms:
        return True

    for role in roles:
        if role in perms:
            return True

    return False


def _get_request_data():
    """
    Get request data depends on content type
    """
    content_type = request.get_header("Content-Type", "")
    if "application/json" in content_type:
        data = request.json
    elif "multipart/form-data" in content_type:
        data = request.forms
    else:
        raise HTTPResponse(status=400, body={"msg": "Weird stuff sent to server"})

    return data


def _validate_data(data, params_list):
    """
    Validate request data based on params_list info
    """
    datatypes = {"str": str, "float": float, "int": int, "bool": bool, "dict": dict, "list": list}

    try:
        for params_dict in params_list:
            name = params_dict["name"]
            required = params_dict["required"]
            datatype = datatypes.get(params_dict["param_type"])
            default = params_dict["default"]

            if required and name not in data.keys():
                raise ValueError(f"{name} is required.")

            if name in data.keys() and not isinstance(data[name], datatype):
                raise ValueError(f"{name} should be instance of the {datatype} type.")

            if not required and name not in data.keys():
                data[name] = default
    except ValueError:
        raise HTTPResponse(status=400, body={"msg": "Invalid Form", "error": format_exc()})


def _filter_data(data, params):
    filtered_data = {key: value for key, value in data.items() if key in params}
    return filtered_data


def _set_context(ctx, params, data):
    for name, param in params.items():
        param_type = param.annotation.__name__ if param.annotation != param.empty else "Unknown"
        default = param.default if param.default != param.empty else "N/A"

        if param_type == "Context":
            data[name] = ctx if default == "N/A" else default
            break

    return data


def tpost(path, roles=None):
    def decorator(func):
        params = signature(func).parameters
        doc_params = _get_doc_params(params)
        _docs.append(dict(
            path=path,
            method='post',
            func=func,
            params=doc_params,
        ))

        @wraps(func)
        @post(path)
        def wrapper(*args, **kwargs):
            if roles and not _auth(roles):
                return HTTPResponse(status=401, body=dict(msg=f"Invalid access. Requires {', '.join(roles)}"))

            req_data = _get_request_data()
            data = req_data if req_data and len(params) > 0 else {}
            data = _filter_data(data, params)
            _validate_data(data, doc_params)

            ctx = Context(
                path=path,
            )
            data = _set_context(ctx, params, data)

            response.content_type = "application/json"
            response.status = 200

            try:
                func_res = func(**data)

                if len(func_res) == 2 and type(func_res) == tuple:
                    response.status = func_res[1]
                    return dumps(func_res[0])

                return dumps(func_res)

            except peewee.DoesNotExist as e:
                e_msg = e.__class__.__name__
                model_name = e_msg.split("DoesNotExist")[0] if len(e_msg.split("DoesNotExist")) > 0 else ""
                response.status = 404

                return dict(msg=f"{model_name} model doesn't exist")

        return wrapper

    return decorator


def get_ip():
    headers = ["X-Real-IP", "X-Forwarded-For", "X-Forwarded-Host"]

    for header in headers:
        if header in request.headers:
            ip = request.headers[header]

            if ',' in ip:
                ip = ip.split(',')[0]

            if not is_ip4(ip):
                continue

            return ip

    return "127.0.0.1"


def get_token():
    if "Authorization" in request.headers:
        return request.headers["Authorization"].split(" ")[1]
    elif "token" in request.cookies:
        return request.cookies["token"]
    elif "multipart/form-data" in str(request.content_type):
        return request.forms.get("authorization")
    return None


class NotFound404(Exception):
    pass


def formatted_headers() -> str:
    """
    This function returns string of request headers
    that don't contain forbidden names.
    """
    forbidden_names = ("key", "auth", "secret", "cookie", "session")
    headers = "\n".join(
        [
            f"{key}: {value}"
            for key, value in request.headers.items()
            if key.lower() not in forbidden_names
        ]
    )

    if request.headers:
        return headers

    return ""


class ErrorHandler:
    def __init__(
        self, message, max_request_per_minute=10, on_error=None
    ):
        self._recent_msgs = []
        self.max_request_per_minute = max_request_per_minute
        self.message = message
        self.on_error = on_error if on_error else self._on_error

    def _on_error(self):
        msg = ""
        try:
            msg += f"{request.path} [{request.method}] {get_ip()}\n\n"
            msg += formatted_headers()
        except:
            msg += (
                f"Failed to generate error message\n{format_exc()}\n\n"
                f"for the error:"
            )

        return msg

    def on_msg(self, msg: str):
        current_date = datetime.now()

        self._recent_msgs = [
            m for m in self._recent_msgs if (current_date - m).total_seconds() <= 60
        ]

        if len(self._recent_msgs) < self.max_request_per_minute:
            self.message(msg)

    def handle(self, callback):
        def wrapper(*args, **kwargs):
            try:
                body = callback(*args, **kwargs)
                return body
            except NotFound404 as e:
                return dict(msg=e.args[0])
            except HTTPResponse as e:
                response.status = getattr(e, "status", None)
                response.headers.update(getattr(e, "headers", {}))
                return getattr(e, "body", {"msg": "Something went wrong"})
            except:  # noqa
                msg = f"{self.on_error()}\n\n{format_exc()}"
                print(msg)
                self.on_msg(msg)
                self._recent_msgs.append(datetime.now())
                return {"msg": "Internal Error"}

        return wrapper


def install_peewee(db):
    @hook("before_request")
    def _db_connect():
        db.connect(reuse_if_open=True)

    @hook("after_request")
    def _db_close():
        if not db.is_closed():
            db.close()


def install_general(prefix='/'):
    @get(f"{prefix}general/ok")
    def ok():
        # event("info", "/general/ok", dict())
        return "ok"

    @get(f"{prefix}general/error")
    def error():
        return 1 / 0

    @get(f"{prefix}general/version")
    def version():
        return dict(msg="ok", content=read("version"))


def install_deploy(path, output, key="", on_invalid_key=None, post_fun=None, merge=False):
    @post(path)
    def deployer():
        if key and request.headers.get("Authorization", "") != f"apitoken {key}":
            if on_invalid_key and callable(on_invalid_key):
                on_invalid_key()
            return "no access"

        with tempfile.TemporaryDirectory() as tmp_dir:
            zip_path = os.path.join(tmp_dir, f'deployer-{uuid4()}.zip')
            request.files.get("file").save(zip_path, overwrite=True)

            with ZipFile(zip_path, "r") as fh:
                if not merge:
                    rmdir(output)

                mkdir(output)
                fh.extractall(output)

            if post_fun and callable(post_fun):
                post_fun()

        return "ok"


def _nice_form(docs_params):
    if not docs_params:
        return []

    props = []
    for prop in docs_params:
        try:
            item = dict(
                name=prop["name"],
                required=prop["required"],
                has_default=prop["default"] != "N/A",
                default=prop["default"] if prop["default"] != "N/A" else "",
                type=prop["param_type"],
            )

            props.append(item)
        except: # noqa
            print(
                f"Error occured during mydocs setup {prop['name']} {format_exc()}"
            )
    return props


def _get_rules(base, docs):
    rules = []

    for doc in docs:
        doc_func = doc['func']
        rules.append(
            dict(
                url=f"{base}{doc['path']}",
                path=doc["path"],
                method=doc["method"],
                doc=str(inspect.getdoc(doc_func) if inspect.getdoc(doc_func) else ""),
                form=_nice_form(doc["params"])
            )
        )

    return rules


def install_docs(path, base):
    # It is important that this is at init else it wont work
    this_dir, this_filename = os.path.split(__file__)
    docs_path = os.path.join(this_dir, "docs.html")
    rules = _get_rules(base, _docs)

    @get(path)
    def mydocs_view():
        with open(docs_path, "r") as f:
            tmpl = SimpleTemplate(f.read())
            return tmpl.render(
                rules=rules,
                base=base,
            )


def install_cors(hosts):
    @route("/<:re:.*>", method="OPTIONS")
    def enable_cors_generic_route():
        """
        This route takes priority over all others. So any request with an OPTIONS
        """
        add_cors_headers()

    @hook("after_request")
    def enable_cors_after_request_hook():
        add_cors_headers()

    def add_cors_headers():
        cors_ok = request.headers["Host"] in hosts

        if cors_ok:
            response.headers["Access-Control-Allow-Origin"] = '*'
            response.headers[
                "Access-Control-Allow-Headers"
            ] = "Content-Type, Content-Length, Accept-Encoding, X-CSRF-Token, Authorization, accept, origin, Cache-Control, X-Requested-With, sentry-trace"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers[
                "Access-Control-Allow-Methods"
            ] = "POST, HEAD,PATCH , OPTIONS, GET, PUT"


def stopwatch(callback):
    def wrapper(*args, **kwargs):
        start = time.time()
        body = callback(*args, **kwargs)
        end = time.time()
        response.headers["X-Time"] = str(end - start)
        return body

    return wrapper


def make_public(funcs, roles=None, prefix=""):
    for func in funcs:
        tpost(f"{prefix}/{func.__name__}", roles=roles)(func)


def install_diskspace_checker(path, disk_path, space):
    @get(path)
    def diskspace_checker():
        if not os.path.exists(disk_path):
            return f"No such file or directory {disk_path}"

        total, used, free = shutil.disk_usage(disk_path)
        free_mb = free / (1024 ** 2) if free > 0 else 0

        if free_mb < space:
            return f"There is no free {space} MB left at {disk_path}."

        return "ok"


