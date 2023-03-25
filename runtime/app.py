import json
import os
import traceback

import boto3
from chalice import Chalice

from chalicelib.chat_history import delete_chat_history, get_chat_history, add_chat_history
from chalicelib.openai_api import generate_chat_response
from chalicelib.telegram import send_chat_action, send_text_message

app = Chalice(app_name='chatgpt-telegram-bot')

UPDATE_MESSAGE_QUEUE = os.getenv('UPDATE_MESSAGE_QUEUE')
UPDATE_MESSAGE_QUEUE_ARN = os.getenv('UPDATE_MESSAGE_QUEUE_ARN')
sqs = boto3.resource('sqs')

commands = [{'command': 'clear', 'description': 'Resets our conversation'}]
clear_command_message = '🤖 Conversation reset. Start anew!'
error_response_message = '⚠️ Apologies, an error occurred. Please try again or contact support if the issue persists.'


@send_chat_action('typing')
def process_message(message):
    chat_id = message['chat_id']
    content = message['content']
    message_id = message['message_id']

    if content == '/start':
        command_message = '\n'.join([f'- `/{command["command"]}`: {command["description"]}' for command in commands])
        response = f'🔹Commands🔹\n{command_message}'
    elif content == '/clear':
        delete_chat_history(chat_id)
        response = clear_command_message
    else:
        chat_history = get_chat_history(chat_id)

        try:
            response, chat_history = generate_chat_response(chat_history, content)
            add_chat_history(chat_id, chat_history)
        except Exception as e:
            app.log.error('Create chat completion error: %s', e)
            app.log.error(traceback.format_exc())
            response = error_response_message

    send_text_message(chat_id, response, message_id)


@app.route('/message', methods=['POST'])
def api_handler():
    body = app.current_request.json_body

    if body is None or 'message' not in body:
        return {'statusCode': 200}

    message = body['message']

    if 'text' in message:
        message_type = 'text'
        message_body = json.dumps(
            {
                'content': message[message_type],
                'chat_id': message['chat']['id'],
                'message_id': message['message_id'],
                'message_type': message_type
            }
        )

        queue = sqs.get_queue_by_name(QueueName=UPDATE_MESSAGE_QUEUE)
        queue.send_message(MessageBody=message_body)


@app.on_sqs_message(queue_arn=UPDATE_MESSAGE_QUEUE_ARN)
def message_handler(event):
    for record in event:
        message = json.loads(record.body)
        process_message(message)
