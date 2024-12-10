# -*- coding: utf-8 -*-
"""
Management command for refreshing the skills associated with xblocks.
"""

import logging

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey, UsageKey

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _

from taxonomy import utils
from taxonomy.choices import ProductTypes
from taxonomy.exceptions import InvalidCommandOptionsError, XBlockMetadataNotFoundError
from taxonomy.models import CourseRunXBlockSkillsTracker, RefreshXBlockSkillsConfig
from taxonomy.providers.course_run_metadata import CourseRunContent
from taxonomy.providers.utils import get_course_run_metadata_provider, get_xblock_metadata_provider
from taxonomy.providers.xblock_metadata import XBlockMetadataProvider

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
        $ # To update all xblocks in 10 unprocessed course runs from discovery
        $ ./manage.py refresh_xblock_skills --all --commit --limit 10
        $ # To update all xblocks in all the courses and mark course completely tagged even if 90% of blocks are tagged.
        $ ./manage.py refresh_xblock_skills --all --commit --success_threshold 0.9
    """
    help = 'Refreshes the skills associated with XBlocks.'
    product_type = ProductTypes.XBlock

    def add_arguments(self, parser):
        """
        Add arguments to the command parser.
        """
        parser.add_argument(
            '--course_run',
            metavar=_('COURSE_RUN_KEY'),
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
            '--success_threshold',
            metavar=_('SUCCESS_THRESHOLD'),
            type=float,
            help=_('Threshold to mark course as completely tagged, i.e. all xblocks are tagged.'),
            default=getattr(settings, "TAXONOMY_XBLOCK_TAGGING_SUCCESS_THRESHOLD", 1.0),
        )
        parser.add_argument(
            '--limit',
            metavar=_('LIMIT'),
            type=int,
            help=_('Only works with --all flag, limits the number of course runs to this number.'),
            default=0,
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

    @staticmethod
    def is_course_run_processed(course_run_key: str):
        return CourseRunXBlockSkillsTracker.objects.filter(course_run_key=course_run_key).exists()

    @staticmethod
    def mark_course_run_completed(
            course_run_key: str,
            success_count: int,
            failure_count: int,
            threshold: float,
    ):
        """
        Add an entry to CourseRunXBlockSkillsTracker table marking the course
        as complete if the ratio of success_count/total >= threshold.
        Marks course complete if total == 0.
        """
        total = success_count + failure_count
        success_ratio = success_count / total if total else 1
        if success_ratio >= threshold:
            LOGGER.info(
                '[TAXONOMY] Marking course run: [%s] as complete as success ratio: [%s] >= threshold: [%s]',
                course_run_key,
                success_ratio,
                threshold
            )
            CourseRunXBlockSkillsTracker.objects.get_or_create(course_run_key=course_run_key)

    def process_course_run(self, course_run: CourseRunContent, xblock_provider: XBlockMetadataProvider, cmd_args: dict):
        """
        Tag all xblocks under given course_run.

        Args:
            course_run: CourseRunContent containing course_run_key.
            xblock_provider: Provider implementation of xblock metadata.
            cmd_args: command line arguments.
        """
        LOGGER.info(f'[TAXONOMY] Refresh xblocks skills process started for course: {course_run.course_run_key}.')
        xblocks = xblock_provider.get_all_xblocks_in_course(course_run.course_run_key)
        success_count, failure_count = utils.refresh_product_skills(
            xblocks,
            cmd_args['commit'],
            self.product_type
        )
        if cmd_args['commit']:
            self.mark_course_run_completed(
                course_run.course_run_key,
                success_count,
                failure_count,
                cmd_args['success_threshold'],
            )

    def handle(self, *args, **options):
        """
        Entry point for management command execution.
        """
        if not (options['args_from_database'] or options['all'] or options['course_run'] or options['xblock']):
            raise InvalidCommandOptionsError(
                'Either course, xblock, args_from_database or all argument must be provided.',
            )

        if options['args_from_database']:
            options = self.get_args_from_database()

        if options['course_run'] and options['xblock']:
            raise InvalidCommandOptionsError('Either course or xblock argument should be provided and not both.')

        LOGGER.info('[TAXONOMY] Refresh XBlock Skills. Options: [%s]', options)

        course_runs = []
        xblocks_from_args = []
        xblock_provider = get_xblock_metadata_provider()
        if options['all']:
            course_runs = get_course_run_metadata_provider().get_all_published_course_runs()
        elif options['course_run']:
            course_runs = [CourseRunContent(course_run_key=course, course_key='') for course in options['course_run']]
        elif options['xblock']:
            valid_usage_keys = set(key for key in options['xblock'] if self.is_valid_key(key, UsageKey, "UsageKey"))
            xblocks_from_args = xblock_provider.get_xblocks(xblock_ids=list(valid_usage_keys))
            if not xblocks_from_args:
                raise XBlockMetadataNotFoundError(
                    'No xblock metadata was found for following xblocks. {}'.format(options['xblock'])
                )
        else:
            raise InvalidCommandOptionsError('Either course, xblock or --all argument must be provided.')

        processed_course_run_count = 0
        for course_run in course_runs:
            if (self.is_valid_key(course_run.course_run_key, CourseKey, "CourseKey")
                    and not self.is_course_run_processed(course_run.course_run_key)):
                self.process_course_run(course_run, xblock_provider, options)
                processed_course_run_count += 1
                if processed_course_run_count >= options["limit"] > 0:
                    LOGGER.info('[TAXONOMY] Completed processing for %s course runs.')
                    break

        if xblocks_from_args:
            LOGGER.info('[TAXONOMY] Refresh XBlock skills process started for xblocks: [%s]', options['xblock'])
            utils.refresh_product_skills(xblocks_from_args, options['commit'], self.product_type)
