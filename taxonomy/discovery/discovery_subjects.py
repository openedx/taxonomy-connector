# -*- coding: utf-8 -*-
"""
Functions related to discovery subjects.
"""

import logging

import requests
from taxonomy.discovery.utils import auth
from django.conf import settings
from urllib.parse import parse_qs, urlparse, urlencode

LOGGER = logging.getLogger(__name__)

async def get_discovery_subjects(url):
    if not url:
        return []

    url_obj = urlparse(url)
    search_params = parse_qs(url_obj.query)
    search_params['exclude_utm'] = '1'
    search_params['format'] = 'json'
    search_params['marketable_enrollable_course_runs_with_archived'] = '1'
    search_params['include_hidden_course_runs'] = '1'

    access_token = await auth(
        settings.EDX.get('EDX_CLIENT_ID'), 
        settings.EDX.get('EDX_CLIENT_SECRET')
    )

    headers = {
        'Accept': 'application/json',
        'Authorization': f'JWT {access_token}',
    }

    url_with_params = f"{url_obj.scheme}://{url_obj.netloc}{url_obj.path}?{urlencode(search_params, doseq=True)}"

    try:
        response = requests.get(url_with_params, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data['next'], data['results']
    except requests.exceptions.RequestException as e:
        LOGGER.error('[TAXONOMY] Error: [%s]', e)
        return None
    
async def get_all_discovery_subjects():
    en_subjects = []
    next_en = 'https://discovery.edx.org/api/v1/subjects/?limit=20'
    while next_en:
        next_url, subjects = await get_discovery_subjects(next_en)
        en_subjects.extend(subjects)
        next_en = next_url

    es_subjects_map = {}
    next_es = 'https://discovery.edx.org/api/v1/subjects/?limit=20&language_code=es'
    while next_es:
        next_url, subjects = await get_discovery_subjects(next_es)
        for subject in subjects:
            es_subjects_map[subject['uuid']] = subject
        next_es = next_url

    all_subjects = [
        {
            'uuid': subject['uuid'],
            'name': subject['name'],
            **subject,
            'labels': {
                'en': subject['name'],
                'es': es_subjects_map.get(subject['uuid'], {}).get('name', ''),
            },
            'subtitles': {
                'en': subject['subtitle'],
                'es': es_subjects_map.get(subject['uuid'], {}).get('subtitle', ''),
            },
            'descriptions': {
                'en': subject['description'],
                'es': es_subjects_map.get(subject['uuid'], {}).get('description', ''),
            },
        }
        for subject in en_subjects
    ]

    return all_subjects
