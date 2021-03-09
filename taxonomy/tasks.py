"""
Celery tasks for taxonomy.
"""
from __future__ import absolute_import, unicode_literals

import logging

from celery import shared_task

from taxonomy import utils
from taxonomy.providers.utils import get_course_metadata_provider

LOGGER = logging.getLogger(__name__)


@shared_task()
def update_course_skills(course_uuids):
    """
    Task to update course skills.

    Arguments:
        course_uuids (list): uuids of courses for which skills needs to be updated
    """
    LOGGER.info('[TAXONOMY] refresh_course_skills task triggered')
    courses = get_course_metadata_provider().get_courses(course_ids=course_uuids)
    if courses:
        utils.refresh_course_skills(courses, should_commit_to_db=True)
    else:
        LOGGER.warning('[TAXONOMY] No course found with uuids [%d] to update skills.', course_uuids)
