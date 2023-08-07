#!/usr/bin/env python3

import os
import shutil
import base64
import json


def check_disk(path: str, space: int = None, message=None) -> str:
    total, used, free = shutil.disk_usage(path)
    percent_used = (used / total) * 100
    percent_free = (free / total) * 100

    used_mb = used / (1024 ** 2) if used > 0 else 0
    free_mb = free / (1024 ** 2) if free > 0 else 0

    available_space_msg = ""

    if space is not None:
        available_space_msg = (
            f"The disk at '{path}' has {space} MB of free space.\n"
            if free_mb >= space
            else f"There is no free {space} MB left at {path}.\n"
        )

    stats = f"Left: {free_mb:.2f} ({percent_free:.2f}%) MB\nUsed: {used_mb:.2f} MB ({percent_used:.2f}%)\n"
    stats += f"'{path}' is running out of space." if percent_used > 90 else f"'{path}' has sufficient space."

    msg = available_space_msg + stats

    if message and callable(message):
        message(msg)

    return msg


def str2int(string):
    try:
        return int(string)
    except:  # noqa
        raise Exception(f"{string} should be int type.")


def read_config(config, mandatory_fields=[]):
    from json import loads

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


def get_password(password):
    if not password:
        password = input("Password: ")

    return password


def encrypt(value, password):
    fernet = create_fernet(password)
    res_value = fernet.encrypt(value.encode()).decode()
    return res_value


def decrypt(value, password):
    from cryptography.fernet import InvalidToken

    try:
        fernet = create_fernet(password)
        res_value = fernet.decrypt(value.encode()).decode()
        return res_value
    except InvalidToken:
        print("Wrong password")


doc = """ttcore

Usage:
  ttcore check_disk <path> [<space>] [--config=<config>]
  ttcore encrypt <value> [<password>]
  ttcore decrypt <value> [<password>]
  ttcore encrypt_file <path> [--new_path=<new_path>] [--password=<password>]
  ttcore decrypt_file <path> [--new_path=<new_path>] [--password=<password>]

Options:
  -h --help     Show this screen.
"""


def cli():
    from docopt import docopt

    arguments = docopt(doc)

    if arguments['check_disk']:
        from .messages import init_message

        default_config = os.path.join(os.path.expanduser("~"), ".ttcore.json")
        free_space = str2int(arguments['<space>']) if arguments['<space>'] else None
        config_path = arguments["--config"] if arguments["--config"] else default_config

        config = read_config(config_path, ["message"])
        message = init_message(config["message"])

        check_disk(arguments['<path>'], free_space, message)

    if arguments['encrypt']:
        password = get_password(arguments['<password>'])
        res_value = encrypt(arguments['<value>'], password)
        print(res_value)

    if arguments['decrypt']:
        password = get_password(arguments['<password>'])
        res_value = decrypt(arguments['<value>'], password)
        print(res_value)

    if arguments['encrypt_file']:
        password = get_password(arguments['--password'])
        data = read_config(arguments['<path>'])

        for key, value in data.items():
            if value.startswith("gAAAAA"):
                continue

            data[key] = encrypt(value, password)

        output_path = arguments['--new_path'] if arguments['--new_path'] else arguments['<path>']

        with open(output_path, 'w') as f:
            f.write(json.dumps(data))

    if arguments['decrypt_file']:
        password = get_password(arguments['--password'])
        data = read_config(arguments['<path>'])

        for key, value in data.items():
            if not value.startswith("gAAAAA"):
                continue

            data[key] = decrypt(value, password)

        output_path = arguments['--new_path'] if arguments['--new_path'] else arguments['<path>']

        with open(output_path, 'w') as f:
            f.write(json.dumps(data))


if __name__ == "__main__":
    cli()
