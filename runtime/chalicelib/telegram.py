import os
from functools import wraps

import requests

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_API_URL = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}'

MAX_TEXT_LENGTH = 4096


def send_message(chat_id, text, message_id):
    json = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown',
        'reply_to_message_id': message_id
    }

    response = requests.post(f'{TELEGRAM_API_URL}/sendMessage', json=json)
    response.raise_for_status()


def send_text_message(chat_id, text, message_id):
    chunks = [text[i:i + MAX_TEXT_LENGTH] for i in range(0, len(text), MAX_TEXT_LENGTH)]

    for chunk in chunks:
        send_message(chat_id, chunk, message_id)


def send_chat_action(action):
    def decorator(func):
        @wraps(func)
        def wrapper(message, *args, **kwargs):
            json = {
                'chat_id': message['chat_id'],
                'action': action,
            }

            requests.post(f'{TELEGRAM_API_URL}/sendChatAction', json=json)
            return func(message, *args, **kwargs)

        return wrapper

    return decorator
