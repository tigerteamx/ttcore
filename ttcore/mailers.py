import requests
from traceback import format_exc
from dataclasses import dataclass
from typing import Callable


@dataclass
class Mail:
    send_from: str
    send_to: str
    subject: str = ""
    body: str = ""


@dataclass
class MailgunData:
    key: str
    domain: str
    in_eu: bool = False


@dataclass
class TelegramData:
    key: str
    chat: str
    on_error: Callable = None


@dataclass
class ConsoleData:
    ...


class MailgunMailer:
    def __init__(self, key, domain, in_eu):
        self.key = key
        self.domain = domain
        self.in_eu = in_eu

    def send(self, mail: Mail):
        if self.in_eu:
            request_url = f"https://api.eu.mailgun.net/v3/{self.domain}/messages"
        else:
            request_url = f"https://api.mailgun.net/v3/{self.domain}/messages"
        req = requests.post(
            request_url,
            auth=("api", self.key),
            data={
                "from": mail.send_from,
                "to": mail.send_to,
                "subject": mail.subject,
                "text": mail.body,
            },
        )

        return req.text if req.status_code != 200 else None


class TelegramMailer:
    def __init__(self, key, chat, on_error=None):
        self.key = key
        self.chat_id = chat
        self.on_error = on_error

    def send(self, mail: Mail):
        try:
            requests.post(
                f"https://api.telegram.org/bot{self.key}/sendMessage",
                json=dict(
                    chat_id=self.chat_id,
                    text=(
                        f"Email\nFrom: {mail.send_from}\nTo: {mail.send_to}\n"
                        f"subject: {mail.subject}\n"
                        f"body: {mail.body}"
                    ),
                ),
            )
            return True
        except:  # noqa
            print(format_exc())
            self.log_error(format_exc())
            return False

    def log_error(self, data):
        if self.on_error and callable(self.on_error):
            self.on_error(data)


class ConsoleMailer:
    def send(self, mail: Mail):
        from pprint import pprint

        pprint(
            {
                "from": mail.send_from,
                "to": mail.send_to,
                "subject": mail.subject,
                "text": mail.body,
            }
        )

        return None


def init_mailer(mailer):
    if isinstance(mailer, TelegramData):
        return TelegramMailer(
            key=mailer.key,
            chat=mailer.chat,
            on_error=mailer.on_error,
        )
    elif isinstance(mailer, MailgunData):
        return MailgunMailer(
            key=mailer.key,
            domain=mailer.domain,
            in_eu=mailer.in_eu,
        )
    elif isinstance(mailer, ConsoleData):
        return ConsoleMailer()

    raise Exception(
        f"Invalid mailer type, expected TelegramData, MailgunData, ConsoleData"
        f"but got {type(mailer)}"
    )
