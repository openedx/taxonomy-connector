"""
This module contains taxonomy related signals handlers.
"""

import logging

from django.dispatch import receiver

from taxonomy.tasks import update_course_skills, update_program_skills, update_xblock_skills

from .signals import UPDATE_COURSE_SKILLS, UPDATE_PROGRAM_SKILLS, UPDATE_XBLOCK_SKILLS

LOGGER = logging.getLogger(__name__)


@receiver(UPDATE_COURSE_SKILLS)
def handle_update_course_skills(sender, course_uuid, **kwargs):  # pylint: disable=unused-argument
    """
    Handle signal and trigger task to update course skills.
    """
    LOGGER.info('[TAXONOMY] UPDATE_COURSE_SKILLS signal received')
    update_course_skills.delay([course_uuid])


@receiver(UPDATE_PROGRAM_SKILLS)
def handle_update_program_skills(sender, program_uuid, **kwargs):  # pylint: disable=unused-argument
    """
    Handle signal and trigger task to update program skills.
    """
    LOGGER.info('[TAXONOMY] UPDATE_PROGRAM_SKILLS signal received')
    update_program_skills.delay([program_uuid])


@receiver(UPDATE_XBLOCK_SKILLS)
def handle_update_xblock_skills(sender, xblock_uuid, **kwargs):  # pylint: disable=unused-argument
    """
    Handle signal and trigger task to update xblock skills.
    """
    LOGGER.info('[TAXONOMY] UPDATE_XBLOCK_SKILLS signal received')
    update_xblock_skills.delay([xblock_uuid])
