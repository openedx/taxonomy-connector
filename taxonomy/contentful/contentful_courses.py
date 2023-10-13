# -*- coding: utf-8 -*-
"""
Sort of functions to sync Courses data from discovery to contentful.
"""

import logging
from amqp import NotFound

from taxonomy.discovery.discovery_courses import get_default_active_program, course_in_prospectus, get_recommended_course_uuids
from contentful_management import Client
from django.conf import settings
from urllib.parse import urlparse

LOGGER = logging.getLogger(__name__)

async def process_discovery_courses(discovery_courses):
    if discovery_courses and len(discovery_courses) > 0:
        for course in discovery_courses:
            LOGGER.info('Syncing course start: [%s] : [%s]', course["title"], course["uuid"])
            await create_or_update_course(course)
            LOGGER.info('Syncing course done: [%s] : [%s]', course["title"], course["uuid"])

async def create_or_update_course(discovery_course):
    client = Client(settings.CONTENTFUL.get('CONTENTFUL_MANAGEMENT_TOKEN'))
    space = client.spaces().find(settings.CONTENTFUL.get('CONTENTFUL_SPACE_ID'))
    environment = space.environments().find(settings.CONTENTFUL.get('CONTENTFUL_ENVIRONMENT'))

    existing_contentful_course = {}
    prospectus_path = None

    try:
        prospectus_path = urlparse(discovery_course['marketing_url'])
        prospectus_path = prospectus_path.path
    except Exception as e:
        LOGGER.error(e)
        return

    try:
        existing_contentful_course = environment.entries().find(discovery_course['uuid'] or '')
    except Exception as e:
        if isinstance(e, NotFound):
            LOGGER.error('Course [%s] not found. Will create it', discovery_course['uuid'])
        else:
            LOGGER.error(e)

    result = course_in_prospectus(discovery_course)
    in_prospectus, is_preview, active_course_run, active_course_runs = (
        result['in_prospectus'],
        result['is_preview'],
        result['active_course_run'],
        result['active_course_runs']
    )

    in_prospectus_and_all_bootcamps = in_prospectus or discovery_course['course_type'] == 'bootcamp-2u'
    full_active_course_runs = [
        course_run for course_run in discovery_course['course_runs'] if course_run['uuid'] in active_course_runs
    ]

    if len(active_course_runs) > 0:
        existing_course_runs = []
        active_course_runs_filter = ','.join(active_course_runs)

        try:
            existing_course_run_entries = environment.entries({
                'content_type': 'courseRun',
                'limit': 200,
                'sys.id[in]': active_course_runs_filter
            })
            existing_course_runs = existing_course_run_entries.items
        except Exception as e:
            if isinstance(e, NotFound):
                LOGGER.error('Course [%s] not found. Will create it', discovery_course['uuid'])
            else:
                LOGGER.error(e)
        
        for existing_course_run in existing_course_runs:
            new_course_run_info = next((course_run for course_run in full_active_course_runs if course_run['uuid'] == existing_course_run.sys['id']), None)
            existing_course_run['fields'] = {
                **existing_course_run['fields'],
                'title': {'en-US': new_course_run_info.get('title')},
                'json': {'en-US': t_dict(new_course_run_info)}
            }

            if not in_prospectus_and_all_bootcamps:
                LOGGER.info('[TAXONOMY] Removing course run: [%s]', existing_course_run.sys['id'])
                try:
                    existing_course_run.unpublish()
                    existing_course_run.delete()
                except Exception as error:
                    LOGGER.error('[TAXONOMY] Error: [%s]', error)
                continue

            LOGGER.info('[TAXONOMY] Updating course run: [%s]', existing_course_run.sys['id'])
            try:
                existing_course_run.save()
                existing_course_run.publish()
            except Exception as error:
                LOGGER.error('[TAXONOMY] Error: [%s]', error)
        
        if not in_prospectus_and_all_bootcamps:
            return

        course_runs_to_create = [course_run for course_run in full_active_course_runs if not any(existing_course_run.sys['id'] == course_run['uuid'] for existing_course_run in existing_course_runs)]

        for active_course_run in course_runs_to_create:
            LOGGER.info('[TAXONOMY] Creating course run: [%s]', active_course_run['uuid'])
            try:
                entry_attributes = {
                    'content_type_id': 'courseRun',
                    'fields': {
                        'title': {'en-US': active_course_run['title']},
                        'json': {'en-US': t_dict(active_course_run)}
                    }
                }
                entry = environment.entries().create(
                    active_course_run['uuid'],
                    entry_attributes
                )
                entry.publish()
            except Exception as error:
                LOGGER.error('[TAXONOMY] Error: [%s]', error)

    is_in_contentful = bool(existing_contentful_course.sys['id'] if existing_contentful_course and existing_contentful_course.sys else None)
    discovery_course['course_runs'] = active_course_runs
    discovery_course['active_course_run'] = active_course_run
    del discovery_course['course_run_statuses']
    discovery_course['owners'] = [owner['uuid'] for owner in discovery_course.get('owners', [])]
    discovery_course['subjects'] = [subject['uuid'] for subject in discovery_course.get('subjects', [])]
    default_active_program = get_default_active_program(discovery_course.get('programs', []))
    discovery_course['active_program'] = default_active_program.get('uuid', '') if default_active_program else ''
    discovery_course['programs'] = [program['uuid'] for program in discovery_course.get('programs', [])]

    # OFAC: mark the course as restricted if any of its active course runs are restricted
    discovery_course['has_ofac_restrictions'] = any(run['has_ofac_restrictions'] for run in full_active_course_runs) if full_active_course_runs else False

    if discovery_course['course_type'] != 'bootcamp-2u':
        del discovery_course['skills']

    if not in_prospectus_and_all_bootcamps and is_in_contentful:
        LOGGER.info('[TAXONOMY] Removing course: [%s]', discovery_course['uuid'])
        try:
            await existing_contentful_course.unpublish().delete()
        except Exception as error:
            LOGGER.error('[TAXONOMY] Error: [%s]', error)

    primary_subject_uuid = discovery_course['subjects'][0] if discovery_course['subjects'] and discovery_course['subjects'][0] else None
    primary_subject = {
        'primarySubject': {
            'en-US': {
                'sys': {
                    'type': 'Link',
                    'linkType': 'Entry',
                    'id': primary_subject_uuid,
                },
            },
        },
    } if primary_subject_uuid else {}
    recommended_course_uuids = await get_recommended_course_uuids(discovery_course['key'])
    recommendations = {
        'recommendations': {
            'en-US': [
                {
                    'sys': {
                        'type': 'Link',
                        'linkType': 'Entry',
                        'id': uuid,
                    }
                }
                for uuid in recommended_course_uuids
            ],
        }
    } if recommended_course_uuids else {}
    new_contentful_course = {
        'fields': {
            'uuid': {'en-US': discovery_course['uuid']},
            'title': {'en-US': discovery_course['title'] or ''},
            'courseType': {'en-US': discovery_course['course_type'] or ''},
            'slug': {'en-US': prospectus_path},
            'json': {'en-US': t_dict(discovery_course)},
            'isPreview': {'en-US': is_preview},
            **primary_subject,
            **recommendations,
        },
    }

    if in_prospectus_and_all_bootcamps and is_in_contentful:
        merged_dict = existing_contentful_course.fields('en-US') | new_contentful_course['fields']
        existing_contentful_course.fields = merged_dict
        LOGGER.info('[TAXONOMY] Updating course: [%s]', discovery_course['uuid'])
        try:
            existing_contentful_course.save()
            existing_contentful_course.publish()
        except Exception as error:
            LOGGER.error('[TAXONOMY] Error: [%s]', error)

    if in_prospectus_and_all_bootcamps and not is_in_contentful:
        LOGGER.info('[TAXONOMY] Creating course: [%s]', discovery_course['uuid'])
        try:
            entry_attributes = {
                'content_type_id': 'course',
                **new_contentful_course
            }
            entry = environment.entries().create(
                discovery_course['uuid'],
                entry_attributes
            )
            entry.publish()
        except Exception as error:
            LOGGER.error('[TAXONOMY] Error: [%s]', error)

def t_dict(d):
   if isinstance(d, list):
      return [t_dict(i) if isinstance(i, (dict, list)) else i for i in d]
   return {to_camel_case(a):t_dict(b) if isinstance(b, (dict, list)) else b for a, b in d.items()}

def to_camel_case(str):
    result = ''
    capitalize_next = False
    for char in str:
        if char == '_':
            capitalize_next = True
        else:
            if capitalize_next:
                result += char.upper()
                capitalize_next = False
            else:
                result += char
    return result
