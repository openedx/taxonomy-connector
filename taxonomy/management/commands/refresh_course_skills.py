# -*- coding: utf-8 -*-
"""
Management command for refreshing the skills associated with courses.
"""

import logging

from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _

from taxonomy import utils
from taxonomy.exceptions import CourseMetadataNotFoundError, InvalidCommandOptionsError
from taxonomy.models import RefreshCourseSkillsConfig
from taxonomy.providers.utils import get_course_metadata_provider

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Command to refresh skills associated with the courses.

    Example usage:
        $ ./manage.py refresh_course_skills --course 'Course1_uuid' --course 'Course2_uuid' --commit
        $ # args-from-database means command line arguments will be picked from the database.
        $ ./manage.py refresh_course_skills --args-from-database
        $ # To update all the courses
        $ ./manage.py refresh_course_skills --all --commit
    """
    help = 'Refreshes the skills associated with courses.'

    def add_arguments(self, parser):
        """
        Add arguments to the command parser.
        """
        parser.add_argument(
            '--course',
            metavar=_('UUID'),
            action='append',
            help=_('Course for mapping to skills.'),
            default=[],
        )
        parser.add_argument(
            '--args-from-database',
            action='store_true',
            help=_('Use arguments from the RefreshCourseSkillsConfig model instead of the command line.'),
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help=_('Create course skill mapping for all the courses.'),
        )
        parser.add_argument(
            '--commit',
            action='store_true',
            default=False,
            help=u'Commits the skills to storage. '
        )

    def get_args_from_database(self):
        """
        Return an options dictionary from the current RefreshCourseSkillsConfig model.
        """
        config = RefreshCourseSkillsConfig.get_solo()
        argv = config.arguments.split()
        parser = self.create_parser('manage.py', 'refresh_course_skills')
        return parser.parse_args(argv).__dict__

    def handle(self, *args, **options):
        """
        Entry point for management command execution.
        """
        if not (options['args_from_database'] or options['all'] or options['course']):
            raise InvalidCommandOptionsError('Either course, args_from_database or all argument must be provided.')

        if options['args_from_database']:
            options = self.get_args_from_database()

        LOGGER.info('[TAXONOMY] Refresh Course Skills. Options: [%s]', options)

        if options['all']:
            courses = get_course_metadata_provider().get_all_courses()
        elif options['course']:
            courses = get_course_metadata_provider().get_courses(course_ids=options['course'])
            if not courses:
                raise CourseMetadataNotFoundError(
                    'No course metadata was found for following courses. {}'.format(options['course'])
                )
        else:
            raise InvalidCommandOptionsError('Either course or all argument must be provided.')

        LOGGER.info('[TAXONOMY] Refresh course skills process started.')
        utils.refresh_course_skills(courses, options['commit'])
