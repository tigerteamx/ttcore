from traceback import format_exc
from dataclasses import dataclass
from typing import Callable, Optional
import requests


@dataclass
class MessengerData:
    ...


@dataclass
class TelegramData(MessengerData):
    key: str
    chat: str
    on_error: Callable = None


class Telegram:
    def __init__(self, key, chat, on_error=None):
        self.key = key
        self.chat = chat
        self.on_error = on_error

    def __call__(self, msg):
        try:
            res = requests.post(
                f"https://api.telegram.org/bot{self.key}/sendMessage",
                json=dict(chat_id=self.chat, text=msg),
            )
            if res.status_code != 200:
                self.log_error(res.text)
            return True
        except:  # noqa
            print(format_exc())
            self.log_error(format_exc())
            return False

    def log_error(self, data):
        if self.on_error and callable(self.on_error):
            self.on_error(data)


class Console:
    def __call__(self, msg):
        print(f'Message "{msg}"')


def init_message(messenger_data: Optional[MessengerData]):
    if isinstance(messenger_data, TelegramData):
        return Telegram(
            key=messenger_data.key,
            chat=messenger_data.chat,
            on_error=messenger_data.on_error,
        )

    return Console()
