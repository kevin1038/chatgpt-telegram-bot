import os

import boto3

CHAT_HISTORY_TABLE = os.getenv('CHAT_HISTORY_TABLE')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(CHAT_HISTORY_TABLE)


def get_chat_history(chat_id):
    response = table.get_item(Key={'ChatID': chat_id})

    if 'Item' in response:
        return response['Item']['ChatHistory']

    return []


def add_chat_history(chat_id, chat_history):
    table.put_item(
        Item={
            'ChatID': chat_id,
            'ChatHistory': chat_history
        }
    )


def delete_chat_history(chat_id):
    table.delete_item(Key={'ChatID': chat_id})
