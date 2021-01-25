"""
This module contains taxonomy related signals handlers.
"""

import logging

from django.dispatch import receiver

from taxonomy.tasks import update_course_skills

from .signals import UPDATE_COURSE_SKILLS

LOGGER = logging.getLogger(__name__)


@receiver(UPDATE_COURSE_SKILLS)
def handle_update_course_skills(sender, course_uuid, **kwargs):  # pylint: disable=unused-argument
    """
    Handle signal and trigger task to update course skills.
    """
    LOGGER.info('[TAXONOMY] UPDATE_COURSE_SKILLS signal received')
    update_course_skills.delay([course_uuid])
