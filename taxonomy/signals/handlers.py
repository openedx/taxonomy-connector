"""
This module contains taxonomy related signals handlers.
"""

import logging

from django.dispatch import receiver
from openedx_events.content_authoring.data import DuplicatedXBlockData, XBlockData
from openedx_events.content_authoring.signals import XBLOCK_DELETED, XBLOCK_DUPLICATED, XBLOCK_PUBLISHED
from openedx_events.learning.data import XBlockSkillVerificationData
from openedx_events.learning.signals import XBLOCK_SKILL_VERIFIED

from taxonomy.tasks import (
    delete_xblock_skills,
    duplicate_xblock_skills,
    update_course_skills,
    update_program_skills,
    update_xblock_skills,
    update_xblock_skills_verification_counts
)

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
    update_xblock_skills.delay([str(xblock_uuid)])


@receiver(XBLOCK_DELETED)
def handle_xblock_deleted(**kwargs):
    """
    Handle signal and trigger task to delete xblock skills.
    """
    LOGGER.info('[TAXONOMY] XBLOCK_DELETED signal received')
    xblock_data = kwargs.get('xblock_info', None)
    if not xblock_data or not isinstance(xblock_data, XBlockData):
        LOGGER.error('[TAXONOMY] Received null or incorrect data from XBLOCK_DELETED.')
        return
    delete_xblock_skills.delay([str(xblock_data.usage_key)])


@receiver(XBLOCK_DUPLICATED)
def handle_xblock_duplicated(**kwargs):
    """
    Handle signal and trigger task to duplicate xblock skills.
    """
    LOGGER.info('[TAXONOMY] XBLOCK_DUPLICATED signal received')
    xblock_data = kwargs.get('xblock_info', None)
    if not xblock_data or not isinstance(xblock_data, DuplicatedXBlockData):
        LOGGER.error('[TAXONOMY] Received null or incorrect data from XBLOCK_DUPLICATED.')
        return
    duplicate_xblock_skills.delay(str(xblock_data.source_usage_key), str(xblock_data.usage_key))


@receiver(XBLOCK_PUBLISHED)
def handle_xblock_published(**kwargs):
    """
    Handle signal and trigger task to update xblock skills.
    """
    LOGGER.info('[TAXONOMY] XBLOCK_PUBLISHED signal received')
    xblock_data = kwargs.get('xblock_info', None)
    if not xblock_data or not isinstance(xblock_data, XBlockData):
        LOGGER.error('[TAXONOMY] Received null or incorrect data from XBLOCK_PUBLISHED.')
        return
    update_xblock_skills.delay([str(xblock_data.usage_key)])


@receiver(XBLOCK_SKILL_VERIFIED)
def handle_xblock_verified(**kwargs):
    """
    Handle signal and trigger task to update xblock skills verified and ignored count.
    """
    LOGGER.info('[TAXONOMY] XBLOCK_SKILL_VERIFIED signal received')
    xblock_data = kwargs.get('xblock_info', None)
    if not xblock_data or not isinstance(xblock_data, XBlockSkillVerificationData):
        LOGGER.error('[TAXONOMY] Received null or incorrect data from XBLOCK_SKILL_VERIFIED.')
        return
    if not xblock_data.verified_skills and not xblock_data.ignored_skills:
        LOGGER.error('[TAXONOMY] Missing verified and ignored skills list.')
        return
    update_xblock_skills_verification_counts.delay(
        str(xblock_data.usage_key),
        xblock_data.verified_skills,
        xblock_data.ignored_skills,
    )
