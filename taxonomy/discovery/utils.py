# -*- coding: utf-8 -*-
"""
Utility functions related to discovery.
"""

import logging
import requests

LOGGER = logging.getLogger(__name__)

async def auth(client_id, client_secret):
    if not client_id or not client_secret:
        raise LOGGER.error('[TAXONOMY] Error: No edx client id or secret provided')

    url = 'https://courses.edx.org/oauth2/access_token'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'token_type': 'jwt',
    }

    response = requests.post(url, headers=headers, data=data)

    if response.status_code == 200:
        access_token = response.json().get('access_token')
        return access_token
    else:
        raise LOGGER.error('[TAXONOMY] Error: [%s], [%s]', response.status_code, response.text)
    