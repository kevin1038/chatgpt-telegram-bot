import os

import openai
import tiktoken

openai.api_key = os.getenv('OPENAI_API_KEY')

model = 'gpt-3.5-turbo'
overall_max_tokens = 4096
max_response_tokens = 1024
prompt_max_tokens = overall_max_tokens - max_response_tokens

system_message = 'You are a helpful assistant.'


def create_chat_completion(messages):
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        max_tokens=max_response_tokens
    )

    return response['choices'][0]['message']['content']


def count_tokens(messages):
    if model == 'gpt-3.5-turbo':
        tokens_per_message = 4
        tokens_per_name = -1
    elif model == 'gpt-4':
        tokens_per_message = 3
        tokens_per_name = 1
    else:
        raise NotImplementedError(f'count_tokens() is not implemented for model {model}.')

    encoding = tiktoken.encoding_for_model(model)
    token_count = 0

    for message in messages:
        token_count += tokens_per_message

        for key, value in message.items():
            token_count += len(encoding.encode(value))

            if key == 'name':
                token_count += tokens_per_name

    token_count += 3
    return token_count


def generate_chat_response(chat_history, user_message):
    if not chat_history:
        chat_history = [{'role': 'system', 'content': system_message}]

    chat_history.append({'role': 'user', 'content': user_message})
    prompt_tokens = count_tokens(chat_history)

    while prompt_tokens > prompt_max_tokens:
        del chat_history[1]
        prompt_tokens = count_tokens(chat_history)

    response = create_chat_completion(chat_history)
    chat_history.append({'role': 'assistant', 'content': response})

    return response, chat_history
