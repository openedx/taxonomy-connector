# -*- coding: utf-8 -*-
"""
Functions related to discovery courses.
"""

import logging

import requests
from utils import auth
from django.conf import settings
from urllib.parse import parse_qs, urlparse

LOGGER = logging.getLogger(__name__)

async def get_courses_page(url):
    if not url:
        return [None, None]

    url_obj = urlparse(url)
    search_params = parse_qs(url_obj.query)
    search_params['exclude_utm'] = '1'
    search_params['format'] = 'json'
    search_params['include_hidden_course_runs'] = '1'
    
    omit_params = [
        'announcement', 'bannerImageUrl', 'canonical_course_run_key',
        'description', 'eligible_for_financial_aid', 'external_key',
        'extra_description', 'first_enrollable_paid_seat_price',
        'go_live_date', 'instructors', 'license', 'marketing_slug',
        'mobile_available', 'modified', 'name', 'original_image',
        'reporting_type'
    ]
    for param in omit_params:
        search_params['omit'] = search_params.get('omit', []) + [param]

    LOGGER.info('[TAXONOMY] Getting courses from: [%s]', url)

    async def make_request(retry=0, new_access_token=None):
        nonlocal url_obj

        options = {
            'method': 'GET',
            'url': url,
            'headers': {
                'Accept': 'application/json',
                'Authorization': f'JWT {new_access_token}' if new_access_token else '',
            },
        }

        response = requests.get(url_obj.geturl(), headers=options['headers'])

        if response.status_code == 401 and retry < 3:
            LOGGER.info('[TAXONOMY] Refreshing access token')
            # Implement the auth function to get a new access token
            new_access_token = await auth(settings.EDX.get('EDX_CLIENT_ID'), settings.EDX.get('EDX_CLIENT_SECRET'))
            options['headers']['Authorization'] = f'JWT {new_access_token}'
            return await make_request(retry + 1, new_access_token)

        if response.ok:
            data = response.json()
            next_url = data.get('next')
            results = data.get('results', [])

            if results:
                return [results, next_url]
            else:
                LOGGER.info('[TAXONOMY] No new updates found')
                return [None, None]

        response.raise_for_status()

    return await make_request()

async def get_recommended_course_uuids(course_key):
    url_obj = urlparse(f'https://discovery.edx.org/api/v1/course_recommendations/{course_key}/')
    search_params = {'omit': ['key', 'title', 'owners', 'image', 'short_description', 'type', 'url_slug', 'course_run_keys', 'marketing_url']}
    
    LOGGER.info('[TAXONOMY] Getting recommended course UUIDs for: [%s]', course_key)

    async def make_request(retry=0, new_access_token=None):
        nonlocal url_obj

        options = {
            'method': 'GET',
            'url': url_obj.geturl(),
            'headers': {
                'Accept': 'application/json',
                'Authorization': f'JWT {new_access_token}' if new_access_token else '',
            },
        }

        response = requests.get(url_obj.geturl(), headers=options['headers'])

        if response.status_code == 401 and retry < 3:
            LOGGER.info('[TAXONOMY] Refreshing access token')
            # Implement the auth function to get a new access token
            new_access_token = await auth(settings.EDX.get('EDX_CLIENT_ID'), settings.EDX.get('EDX_CLIENT_SECRET'))
            options['headers']['Authorization'] = f'JWT {new_access_token}'
            return await make_request(retry + 1, new_access_token)

        if response.ok:
            data = response.json()
            recommendations = data.get('recommendations', [])

            if recommendations:
                return [rec['uuid'] for rec in recommendations]

            return []

        if response.status_code == 404:
            return []

        response.raise_for_status()

    return await make_request()

def course_in_prospectus(course):
    COURSE_RUN_STATUS_REVIEWED = 'reviewed'
    COURSE_RUN_AVAILABILITY_ARCHIVED = 'archived'

    def is_archived(course_run):
        if course_run.get('availability'):
            return course_run['availability'].lower() == COURSE_RUN_AVAILABILITY_ARCHIVED
        return False

    active_course_runs = [
        course_run for course_run in course['course_runs']
        if course_run['uuid'] == course['advertised_course_run_uuid'] or (
            course_run['is_marketable']
            and course_run['is_enrollable']
            and not is_archived(course_run)
        )
    ]

    advertised_course_run = next(
        (
            course_run
            for course_run in active_course_runs
            if course_run['uuid'] == course['advertised_course_run_uuid']
        ),
        None,
    )

    if (
        course.get('course_run_statuses')
        and len(course['course_run_statuses']) == 1
        and course['course_run_statuses'][0].lower() == COURSE_RUN_STATUS_REVIEWED
    ):
        active_course_run_uuid = next(
            (
                course_run['uuid']
                for course_run in course['course_runs']
                if course_run.get('status', '').lower() == COURSE_RUN_STATUS_REVIEWED
            ),
            None,
        )
        return {
            'in_prospectus': True,
            'active_course_run': active_course_run_uuid,
            'active_course_runs': [active_course_run_uuid],
            'is_preview': True,
        }

    return {
        'in_prospectus': bool(advertised_course_run),
        'active_course_run': advertised_course_run['uuid'] if advertised_course_run else None,
        'active_course_runs': [course_run['uuid'] for course_run in active_course_runs],
        'is_preview': not advertised_course_run,
    }

def get_default_active_program(programs):
    def sort_programs_by_preferred_type(programs):
        if len(programs) < 2:
            return programs
        return sorted(programs, key=lambda x: x['type'].lower())

    sorted_programs = sort_programs_by_preferred_type(programs)
    if len(sorted_programs) < 2:
        return sorted_programs[0] if sorted_programs else {}

    preferred_type_program = next(
        (
            program
            for program in sorted_programs
            if program['type'].lower() in ['micromasters', 'professional certificate']
        ),
        None,
    )

    if preferred_type_program:
        return preferred_type_program

    return sorted_programs[0] if sorted_programs else {}
