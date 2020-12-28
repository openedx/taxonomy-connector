"""
Celery tasks for taxonomy.
"""
from __future__ import absolute_import, unicode_literals

from celery import shared_task

from taxonomy import utils


@shared_task()
def update_course_skills(course_uuid):
    """
    Task to update course skills.
    """
    utils.refresh_course_skills(
        {
            'course': [course_uuid],
            'commit': True,
        }
    )
