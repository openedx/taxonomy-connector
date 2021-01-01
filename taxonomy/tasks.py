"""
Celery tasks for taxonomy.
"""
from __future__ import absolute_import, unicode_literals

from celery import shared_task

from taxonomy import utils


@shared_task()
def update_course_skills(course_uuids):
    """
    Task to update course skills.

    Arguments:
        course_uuids (list): uuids of courses for which skills needs to be updated
    """
    utils.refresh_course_skills(
        {
            'course': course_uuids,
            'commit': True,
        }
    )
