"""
Celery tasks for taxonomy.
"""
from __future__ import absolute_import, unicode_literals

import logging

from celery import shared_task

from taxonomy import utils
from taxonomy.choices import ProductTypes
from taxonomy.providers.utils import (
    get_course_metadata_provider,
    get_program_metadata_provider,
    get_xblock_metadata_provider
)

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
        utils.refresh_product_skills(courses, True, ProductTypes.Course)
    else:
        LOGGER.warning('[TAXONOMY] No course found with uuids [%d] to update skills.', course_uuids)


@shared_task()
def update_program_skills(program_uuids):
    """
    Task to update program skills.

    Arguments:
        program_uuids (list): uuids of programs for which skills needs to be updated
    """
    LOGGER.info('[TAXONOMY] refresh_program_skills task triggered')
    programs = get_program_metadata_provider().get_programs(program_ids=program_uuids)
    if programs:
        utils.refresh_product_skills(programs, True, ProductTypes.Program)
    else:
        LOGGER.warning('[TAXONOMY] No program found with uuids [%d] to update skills.', program_uuids)


@shared_task()
def update_xblock_skills(xblock_uuids):
    """
    Task to update xblock skills.

    Arguments:
        xblock_uuids (list): uuids of xblocks for which skills needs to be updated
    """
    LOGGER.info('[TAXONOMY] refresh_xblock_skills task triggered')
    xblocks = get_xblock_metadata_provider().get_xblocks(xblock_ids=xblock_uuids)
    if xblocks:
        utils.refresh_product_skills(xblocks, True, ProductTypes.XBlock)
    else:
        LOGGER.warning('[TAXONOMY] No xblock found with uuids [%d] to update skills.', xblock_uuids)
