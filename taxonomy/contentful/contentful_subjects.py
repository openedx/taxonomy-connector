# -*- coding: utf-8 -*-
"""
Sort of functions to sync Subjects data from discovery to contentful.
"""

import logging

from taxonomy.discovery.discovery_subjects import get_all_discovery_subjects
from contentful_management import Client
from django.conf import settings
from camelcase import camelcase
from deepdiff import DeepDiff

LOGGER = logging.getLogger(__name__)

async def process_discovery_subjects():
    client = Client(settings.CONTENTFUL.get('CONTENTFUL_MANAGEMENT_TOKEN'))
    space = client.spaces().find(settings.CONTENTFUL.get('CONTENTFUL_SPACE_ID'))
    environment = space.environments().find(settings.CONTENTFUL.get('CONTENTFUL_ENVIRONMENT'))

    limit = 100
    skip = 0
    total = 0
    existing_subjects_map = {}

    while skip < total:
        contentful_subjects = await environment.entries({
            'content_type': 'subject',
            'limit': limit,
            'skip': skip,
        })

        total = contentful_subjects.total
        skip += limit

        for subject in contentful_subjects:
            existing_subjects_map[subject.id] = subject
        
    discovery_subjects = await get_all_discovery_subjects()

    if not discovery_subjects or len(discovery_subjects) == 0:
        return
    
    for subject in discovery_subjects:
        existing_contentful_course = existing_subjects_map.get(subject['uuid'])
        contentful_subject_attributes = {
            'content_type_id': 'subject',
            'fields': {
                'uuid': {'en-US': subject['uuid']},
                'name': {'en-US': subject['name'] or ''},
                'json': {'en-US': camelcase(subject, {'deep': True})},
            },
        }

        if existing_contentful_course.get('sys', {}).get('id'):
            if DeepDiff(camelcase(subject, {'deep': True}), existing_contentful_course.fields['json']['en-US']) == {}:
                continue

            existing_contentful_course['fields'].update(contentful_subject_attributes['fields'])
            await existing_contentful_course.save()
            await existing_contentful_course.publish()
            LOGGER.info('[TAXONOMY] Updated subject: [%s] : [%s]', subject['name'], subject['uuid'])
        else:
            entry = await environment.entries().create(
                subject['uuid'],
                contentful_subject_attributes
            )
            await entry.publish()
            LOGGER.info('[TAXONOMY] Created subject: [%s] : [%s]', subject['name'], subject['uuid'])
            