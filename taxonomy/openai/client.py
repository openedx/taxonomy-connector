"""CHAT_COMPLETION_API client"""
import json
import logging

import requests

from django.conf import settings

log = logging.getLogger(__name__)


def chat_completion(prompt):
    """
    Pass message list to chat endpoint, as defined by the CHAT_COMPLETION_API setting.
    Arguments:
        prompt (str): chatGPT prompt
    """
    completion_endpoint = settings.CHAT_COMPLETION_API
    completion_endpoint_key = settings.CHAT_COMPLETION_API_KEY
    headers = {'Content-Type': 'application/json', 'x-api-key': completion_endpoint_key}
    connect_timeout = getattr(settings, 'CHAT_COMPLETION_API_CONNECT_TIMEOUT', 1)
    read_timeout = getattr(settings, 'CHAT_COMPLETION_API_READ_TIMEOUT', 15)
    body = {'message_list': [{'role': 'assistant', 'content': prompt},]}
    response = requests.post(
        completion_endpoint,
        headers=headers,
        data=json.dumps(body),
        timeout=(connect_timeout, read_timeout)
    )
    chat = response.json().get('content')
    return chat
