#!/usr/bin/env python3

import os
import shutil
from json import dumps
from getpass import getpass

from .utils import read_config


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


def get_password(password):
    if not password:
        password = getpass("Password: ")

    return password


doc = """ttcore

Usage:
  ttcore check_disk <path> [<space>] [--config=<config>]
  ttcore encrypt <value> [<password>]
  ttcore decrypt <value> [<password>]
  ttcore encrypt_file <path> [--output_path=<output_path>] [--password=<password>] [--depth=<depth>]
  ttcore decrypt_file <path> [--output_path=<output_path>] [--password=<password>] [--depth=<depth>]

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
        from .utils import encrypt

        password = get_password(arguments['<password>'])
        res_value = encrypt(arguments['<value>'], password)
        print(res_value)

    if arguments['decrypt']:
        from .utils import decrypt

        password = get_password(arguments['<password>'])
        res_value = decrypt(arguments['<value>'], password)
        print(res_value)

    if arguments['encrypt_file']:
        from .utils import encrypt_dict

        password = get_password(arguments['--password'])
        depth = str2int(arguments['--depth']) if arguments['--depth'] else 2
        config = read_config(arguments['<path>'])
        data = encrypt_dict(config, password, depth)
        output_path = arguments['--output_path'] if arguments['--output_path'] else arguments['<path>']

        with open(output_path, 'w') as f:
            f.write(dumps(data))

    if arguments['decrypt_file']:
        from .utils import decrypt_dict

        password = get_password(arguments['--password'])
        depth = str2int(arguments['--depth']) if arguments['--depth'] else 2
        config = read_config(arguments['<path>'])
        data = decrypt_dict(config, password, depth)
        output_path = arguments['--output_path'] if arguments['--output_path'] else arguments['<path>']

        with open(output_path, 'w') as f:
            f.write(dumps(data))


if __name__ == "__main__":
    cli()
