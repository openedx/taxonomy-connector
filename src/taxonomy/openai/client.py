"""CHAT_COMPLETION_API client"""
import json
import logging

import requests

from django.conf import settings

log = logging.getLogger(__name__)


def chat_completion(prompt, system_message):
    """
    Pass message list to chat endpoint, as defined by the XPERT_AI_API_V2 setting.
    Arguments:
        prompt (str): chatGPT prompt
        system_message (str): system message to be used in the chat
    Returns:
        str: response from the chat completion API. If the API fails, an empty string is returned.
    """
    connect_timeout = getattr(settings, 'CHAT_COMPLETION_API_CONNECT_TIMEOUT', 1)
    read_timeout = getattr(settings, 'CHAT_COMPLETION_API_READ_TIMEOUT', 15)
    body = {
        'messages': [{'role': 'user', 'content': prompt},],
        'client_id': settings.XPERT_AI_CLIENT_ID,
        'system_message': system_message,
    }
    try:
        response = requests.post(
            settings.XPERT_AI_API_V2,
            headers={'Content-Type': 'application/json'},
            data=json.dumps(body),
            timeout=(connect_timeout, read_timeout)
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        log.error(
            'Error in chat completion API request: %s, %s',
            e,
            body.get('messages')
        )
        raise e
    try:
        return response.json()[0]['content']
    except (KeyError, ValueError, TypeError, IndexError, AttributeError) as e:
        log.error(
            'Error in processing chat completion API response: %s, %s',
            e,
            body.get('messages')
        )
        raise e
