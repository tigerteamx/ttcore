from traceback import format_exc
import requests


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


def init_message(settings):
    message_type = settings.get('type', '')

    if message_type == "console":
        return Console()
    elif message_type == "telegram":
        return Telegram(settings['key'], settings['chat'])
    else:
        raise Exception("Invalid settings for Deepl")

