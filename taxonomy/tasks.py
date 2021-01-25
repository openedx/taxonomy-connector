"""
Celery tasks for taxonomy.
"""
from __future__ import absolute_import, unicode_literals

import logging

from celery import shared_task

from taxonomy import utils

LOGGER = logging.getLogger(__name__)


@shared_task()
def update_course_skills(course_uuids):
    """
    Task to update course skills.

    Arguments:
        course_uuids (list): uuids of courses for which skills needs to be updated
    """
    LOGGER.info('[TAXONOMY] refresh_course_skills task triggered')
    utils.refresh_course_skills(
        {
            'course': course_uuids,
            'commit': True,
        }
    )
