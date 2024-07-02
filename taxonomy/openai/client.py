"""CHAT_COMPLETION_API client"""
import json
import logging

import requests
from requests.exceptions import ConnectTimeout

from django.conf import settings

log = logging.getLogger(__name__)


def chat_completion(prompt):
    """
    Pass message list to chat endpoint, as defined by the CHAT_COMPLETION_API setting.
    Arguments:
        prompt (str): chatGPT prompt
    """
    completion_endpoint = getattr(settings, 'CHAT_COMPLETION_API', None)
    completion_endpoint_key = getattr(settings, 'CHAT_COMPLETION_API_KEY', None)
    if completion_endpoint and completion_endpoint_key:
        headers = {'Content-Type': 'application/json', 'x-api-key': completion_endpoint_key}
        connect_timeout = getattr(settings, 'CHAT_COMPLETION_API_CONNECT_TIMEOUT', 1)
        read_timeout = getattr(settings, 'CHAT_COMPLETION_API_READ_TIMEOUT', 15)
        body = {'message_list': [{'role': 'assistant', 'content': prompt},]}
        try:
            response = requests.post(
                completion_endpoint,
                headers=headers,
                data=json.dumps(body),
                timeout=(connect_timeout, read_timeout)
            )
            chat = response.json()
        except (ConnectTimeout, ConnectionError) as e:
            error_message = str(e)
            connection_message = 'Failed to connect to chat completion API.'
            log.error(
                '%(connection_message)s %(error)s',
                {'connection_message': connection_message, 'error': error_message}
            )
            chat = connection_message
    else:
        chat = 'Completion endpoint is not defined.'

    return chat
