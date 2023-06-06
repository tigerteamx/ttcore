#!/usr/bin/env python3

import shutil
import json

from docopt import docopt

from .messages import init_message


def check_disk(path: str, config: dict = None) -> str:
    total, used, free = shutil.disk_usage(path)
    percent_used = (used / total) * 100

    bytes_in_gb = 1000000000

    used_gb = used / bytes_in_gb if used > 0 else 0
    free_gb = free / bytes_in_gb if free > 0 else 0

    msg = f"The disk at '{path}' has sufficient space:" if percent_used <= 90 else f"The disk at '{path}' is running out of space:"
    res_msg = f"{msg} ({percent_used:.2f}%)\nLeft: {free_gb:.2f} GB\nUsed: {used_gb:.2f} GB\n"

    if not (config and config.get("message", None)):
        return res_msg

    message = init_message(config["message"])
    message(res_msg)

    return res_msg


doc = """ttcore

Usage:
  ttcore check_disk <path> [--config=<config>]

Options:
  -h --help     Show this screen.
"""


def get_config(config):
    with open(config, "r") as f:
        return json.loads(f.read())


def cli():
    arguments = docopt(doc)

    if arguments['check_disk']:
        config = get_config(arguments["--config"]) if arguments["--config"] else None
        check_disk(arguments['<path>'], config)


if __name__ == "__main__":
    cli()
