import pathlib
import shutil
import re
import json as _json_internal
from decimal import Decimal
from datetime import datetime, date
import base64
import unicodedata
import os
from traceback import format_exc


def mkdir(path):
    return pathlib.Path(path).mkdir(parents=True, exist_ok=True)


def mkdir_for_file(path):
    return pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)


def rmdir(path):
    shutil.rmtree(path, ignore_errors=True)


class CustomEncoder(_json_internal.JSONEncoder):
    def default(self, o):  # noqa
        if type(o) == datetime and o is not None:
            return str(o.timestamp())

        if type(o) == Decimal and o is not None:
            return str(o)

        if type(o) == set:
            return list(o)

        if type(o) == date:
            return o.isoformat()

        raise Exception("Cannot encode json for result")


def safe_loads(data, default=None):
    try:
        return _json_internal.loads(data)
    except:  # noqa
        if default is None:
            return {}
        return default


def loads(data):
    return _json_internal.loads(data)


def dumps(data, indent=None):
    return _json_internal.dumps(
        data,
        indent=indent,
        cls=CustomEncoder,
    )


def is_ip4(address: str) -> bool:
    if isinstance(address, str):
        pattern = r"^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){4}$"
        return re.match(pattern, address) is not None
    return False


def read(fn):
    with open(fn, "r") as f:
        return f.read()


def sanitize(filename):
    """Return a fairly safe version of the filename.

    We don't limit ourselves to ascii, because we want to keep municipality
    names, etc, but we do want to get rid of anything potentially harmful,
    and make sure we do not exceed Windows filename length limits.
    Hence a less safe blacklist, rather than a whitelist.

    Source: https://gitlab.com/jplusplus/sanitize-filename
    """
    blacklist = ["\\", "/", ":", "*", "?", "\"", "<", ">", "|", "\0"]
    reserved = [
        "CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5",
        "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4", "LPT5",
        "LPT6", "LPT7", "LPT8", "LPT9",
    ]  # Reserved words on Windows
    filename = "".join(c for c in filename if c not in blacklist)
    # Remove all charcters below code point 32
    filename = "".join(c for c in filename if 31 < ord(c))
    filename = unicodedata.normalize("NFKD", filename)
    filename = filename.rstrip(". ")  # Windows does not allow these at end
    filename = filename.strip()
    if all([x == "." for x in filename]):
        filename = "__" + filename
    if filename in reserved:
        filename = "__" + filename
    if len(filename) == 0:
        filename = "__"
    if len(filename) > 255:
        parts = re.split(r"/|\\", filename)[-1].split(".")
        if len(parts) > 1:
            ext = "." + parts.pop()
            filename = filename[:-len(ext)]
        else:
            ext = ""
        if filename == "":
            filename = "__"
        if len(ext) > 254:
            ext = ext[254:]
        maxl = 255 - len(ext)
        filename = filename[:maxl]
        filename = filename + ext
        # Re-check last character (if there was no extension)
        filename = filename.rstrip(". ")
        if len(filename) == 0:
            filename = "__"
    return filename


def str_or_exception(d, key):
    if key in d:
        return d[key]

    raise Exception(f"Expected {key} but not found")


def read_config(config, mandatory_fields=[]):
    if not os.path.isfile(config):
        raise Exception(f"{config} doesn't exist.")

    with open(config, "r") as f:
        content = loads(f.read())

    for field in mandatory_fields:
        if field not in content:
            raise Exception(f"There is no {field} field found in the {config} file.")

    return content


def create_fernet(password):
    from cryptography.fernet import Fernet
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=b"salt", iterations=100000, backend=default_backend())
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))

    return Fernet(key)


def encrypt(value, password):
    try:
        fernet = create_fernet(password)
        res_value = fernet.encrypt(value.encode()).decode()
        return res_value
    except:  # noqa
        print("Something went wrong", format_exc())

    return value


def decrypt(value, password):
    from cryptography.fernet import InvalidToken

    try:
        fernet = create_fernet(password)
        res_value = fernet.decrypt(value.encode()).decode()
        return res_value
    except InvalidToken:
        print("Wrong password")
    except: # noqa
        print("Something went wrong", format_exc())

    return value


def encrypt_dict(data, password, max_depth, current_depth=0):
    encrypted_data = {}

    for key, value in data.items():
        if isinstance(value, dict) and current_depth < max_depth:
            encrypted_data[key] = encrypt_dict(value, password, max_depth, current_depth + 1)
        elif isinstance(value, str) and not value.startswith("gAAAAA"):
            encrypted_data[key] = encrypt(value, password)
        else:
            encrypted_data[key] = value

    return encrypted_data


def decrypt_dict(data, password, max_depth, current_depth=0):
    decrypted_data = {}

    for key, value in data.items():
        if isinstance(value, dict) and current_depth < max_depth:
            decrypted_data[key] = decrypt_dict(value, password, max_depth, current_depth + 1)
        elif isinstance(value, str) and value.startswith("gAAAAA"):
            decrypted_data[key] = decrypt(value, password)
        else:
            decrypted_data[key] = value

    return decrypted_data
