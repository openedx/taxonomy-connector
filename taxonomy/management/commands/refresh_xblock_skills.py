# -*- coding: utf-8 -*-
"""
Management command for refreshing the skills associated with xblocks.
"""

import logging

from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey, UsageKey

from taxonomy import utils
from taxonomy.choices import ProductTypes
from taxonomy.exceptions import InvalidCommandOptionsError, XBlockMetadataNotFoundError
from taxonomy.models import RefreshXBlockSkillsConfig
from taxonomy.providers.utils import get_course_metadata_provider, get_xblock_metadata_provider

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Command to refresh skills associated with the XBlocks.

    Example usage:
        $ ./manage.py refresh_xblock_skills --xblock 'xblock-usage-key1' --xblock 'xblock-usage-key2' --commit
        $ # To refresh all xblock skills under given courses.
        $ ./manage.py refresh_xblock_skills --course 'course-v1:edX+DemoX+1' --course 'course-v1:edX+DemoY+1' --commit
        $ # args-from-database means command line arguments will be picked from the database.
        $ ./manage.py refresh_xblock_skills --args-from-database
        $ # To update all xblocks in all the courses
        $ ./manage.py refresh_xblock_skills --all --commit
    """
    help = 'Refreshes the skills associated with XBlocks.'
    product_type = ProductTypes.XBlock

    def add_arguments(self, parser):
        """
        Add arguments to the command parser.
        """
        parser.add_argument(
            '--course',
            metavar=_('COURSE_KEY'),
            action='append',
            help=_('Update skills for XBlocks under given course keys. For eg. course-v1:edX+DemoX.1+2014'),
            default=[],
        )
        parser.add_argument(
            '--xblock',
            metavar=_('USAGE_KEY'),
            action='append',
            help=_('Update skills for given Xblock usage keys.'),
            default=[],
        )
        parser.add_argument(
            '--args-from-database',
            action='store_true',
            help=_('Use arguments from the RefreshXBlockSkillsConfig model instead of the command line.'),
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help=_('Create xblock skill mapping for all xblocks in all the courses.'),
        )
        parser.add_argument(
            '--commit',
            action='store_true',
            default=False,
            help=_('Commits the skills to storage.')
        )

    def get_args_from_database(self):
        """
        Return an options dictionary from the current RefreshXBlockSkillsConfig model.
        """
        config = RefreshXBlockSkillsConfig.get_solo()
        argv = config.arguments.split()
        parser = self.create_parser('manage.py', 'refresh_xblock_skills')
        return parser.parse_args(argv).__dict__

    @staticmethod
    def is_valid_key(key, key_cls, key_cls_str):
        """
        Validates usage and course keys.
        """
        try:
            key_cls.from_string(key)
            return True
        except InvalidKeyError:
            LOGGER.error('[TAXONOMY] Invalid %s: [%s]', key_cls_str, key)
        return False

    def handle(self, *args, **options):
        """
        Entry point for management command execution.
        """
        if not (options['args_from_database'] or options['all'] or options['course'] or options['xblock']):
            raise InvalidCommandOptionsError(
                'Either course, xblock, args_from_database or all argument must be provided.',
            )

        if options['args_from_database']:
            options = self.get_args_from_database()

        if options['course'] and options['xblock']:
            raise InvalidCommandOptionsError('Either course or xblock argument should be provided and not both.')

        LOGGER.info('[TAXONOMY] Refresh XBlock Skills. Options: [%s]', options)

        courses = []
        xblocks_from_args = []
        xblock_provider = get_xblock_metadata_provider()
        if options['all']:
            courses = get_course_metadata_provider().get_all_courses()
        elif options['course']:
            courses = [{"key": course} for course in options['course']]
        elif options['xblock']:
            valid_usage_keys = set(key for key in options['xblock'] if self.is_valid_key(key, UsageKey, "UsageKey"))
            xblocks_from_args = xblock_provider.get_xblocks(xblock_ids=list(valid_usage_keys))
            if not xblocks_from_args:
                raise XBlockMetadataNotFoundError(
                    'No xblock metadata was found for following xblocks. {}'.format(options['xblock'])
                )
        else:
            raise InvalidCommandOptionsError('Either course, xblock or --all argument must be provided.')

        for course in courses:
            course_key = course.get("key")
            if self.is_valid_key(course_key, CourseKey, "CourseKey"):
                xblocks = xblock_provider.get_all_xblocks_in_course(course_key)
                LOGGER.info('[TAXONOMY] Refresh xblocks skills process started for course: {course_key}.')
                utils.refresh_product_skills(xblocks, options['commit'], self.product_type)

        if xblocks_from_args:
            LOGGER.info('[TAXONOMY] Refresh XBlock skills process started for xblocks: [%s]', options['xblock'])
            utils.refresh_product_skills(xblocks_from_args, options['commit'], self.product_type)
