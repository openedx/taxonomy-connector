"""CHAT_COMPLETION_API client"""
import json
import logging

import requests

from django.conf import settings

log = logging.getLogger(__name__)


def chat_completion(prompt, system_message=settings.XPERT_DEFAULT_SYSTEM_MESSAGE):
    """
    Pass message list to chat endpoint, as defined by the CHAT_COMPLETION_API_V2 setting.
    Arguments:
        prompt (str): chatGPT prompt
        system_message (str): system message to be used in the chat
    """
    completion_endpoint = settings.CHAT_COMPLETION_API_V2
    headers = {'Content-Type': 'application/json'}
    connect_timeout = getattr(settings, 'CHAT_COMPLETION_API_CONNECT_TIMEOUT', 1)
    read_timeout = getattr(settings, 'CHAT_COMPLETION_API_READ_TIMEOUT', 15)
    body = {
        'messages': [{'role': 'assistant', 'content': prompt},],
        'client_id': settings.XPERT_CLIENT_ID,
        'system_message': system_message,
    }
    response = requests.post(
        completion_endpoint,
        headers=headers,
        data=json.dumps(body),
        timeout=(connect_timeout, read_timeout)
    )

    if response.status_code != 200:
        log.error(
            'Error in chat completion API: %s, %s',
            response.status_code,
            response.text
        )
        return ''

    return response.json()[0].get('content')
