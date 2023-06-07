#!/usr/bin/env python3

import os
import shutil


def check_disk(path: str, space: float = None, message=None) -> str:
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


doc = """ttcore

Usage:
  ttcore check_disk <path> [<space>] [--config=<config>]

Options:
  -h --help     Show this screen.
"""


def str2float(string):
    try:
        return float(string)
    except:  # noqa
        raise Exception(f"{string} should be float type.")


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


def cli():
    from docopt import docopt

    from .messages import init_message

    arguments = docopt(doc)

    if arguments['check_disk']:
        default_config = os.path.join(os.path.expanduser("~"), ".ttcore.json")
        free_space = str2float(arguments['<space>']) if arguments['<space>'] else None
        config_path = arguments["--config"] if arguments["--config"] else default_config

        config = read_config(config_path, ["message"])
        message = init_message(config["message"])

        check_disk(arguments['<path>'], free_space, message)


if __name__ == "__main__":
    cli()
