# -*- coding: utf-8 -*-
"""
Management command for refreshing the skills associated with courses.
"""

import logging

from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import gettext as _

from taxonomy.emsi_client import EMSISkillsApiClient
from taxonomy.exceptions import TaxonomyAPIError
from taxonomy.models import CourseSkills, RefreshCourseSkillsConfig, Skill
from taxonomy.providers.utils import get_course_metadata_provider

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    """
        Example usage:
            $ ./manage.py refresh_course_skills --course 'Course1_uuid' --course 'Course2_uuid' --commit
            $ ./manage.py refresh_course_skills --args-from-database
        """
    help = 'Refreshes the skills associated with courses.'

    def __init__(self, *args, **kwargs):
        """
        Initialize an instance of course metadata provider to be used by the management command.
        """
        super(Command, self).__init__(*args, **kwargs)
        self.course_metadata_provider = get_course_metadata_provider()

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
            '--commit',
            action='store_true',
            default=False,
            help=u'Commits the skills to storage. '
        )

    def get_args_from_database(self):
        """ Returns an options dictionary from the current RefreshCourseSkillsConfig model. """
        config = RefreshCourseSkillsConfig.get_solo()
        argv = config.arguments.split()
        parser = self.create_parser('manage.py', 'refresh_course_skills')
        return parser.parse_args(argv).__dict__

    def _update_skills_data(self, course_key, confidence, skill_data):
        """
        Persist the skills data
        """
        skill, __ = Skill.objects.update_or_create(**skill_data)
        CourseSkills.objects.update_or_create(
            course_id=course_key,
            skill=skill,
            confidence=confidence
        )

    def _refresh_skills(self, options):
        """
        Refreshes the skills associated with the provided courses
        """
        courses = self.course_metadata_provider.get_courses(course_ids=options['course'])

        if not courses:
            raise CommandError(_('No courses found. Did you specify an argument?'))

        failures = set()
        client = EMSISkillsApiClient()
        for course in courses:
            course_description = course['full_description']

            if course_description:
                try:
                    course_skills = client.get_course_skills(course_description)
                except TaxonomyAPIError:
                    LOGGER.error('Taxonomy API Error for course_key: %s', course['key'])
                    failures.add((course['uuid'], course['key']))
                else:
                    failed_records = self._process_skills_data(course, course_skills, options['commit'])
                    failures.update(failed_records)
        if failures:
            keys = sorted('{key} ({uuid})'.format(key=course_key, uuid=uuid) for uuid, course_key in failures)
            raise CommandError(
                _('Could not refresh skills for the following courses: {course_keys}').format(
                    course_keys=', '.join(keys)
                )
            )

    def _process_skills_data(self, course, course_skills, should_commit_to_db):
        """
        Process skills data returned by the EMSI service and update databased.

        Arguments:
            course (dict): Dictionary containing course data whose skills are being processed.
            course_skills (dict): Course skills data returned by the EMSI API.
            should_commit_to_db (bool): Boolean indicating whether data should be committed to database.
        """
        failures = set()

        for record in course_skills['data']:
            try:
                confidence = float(record['confidence'])
                skill = record['skill']
                skill_data = {
                    'external_id': skill['id'],
                    'name': skill['name'],
                    'info_url': skill['infoUrl'],
                    'type_id': skill['type']['id'],
                    'type_name': skill['type']['name'],
                }
                if should_commit_to_db:
                    self._update_skills_data(course['key'], confidence, skill_data)
            except KeyError:
                LOGGER.error('Missing keys in skills data for course_key: %s', course['key'])
                failures.add((course['uuid'], course['key']))
            except (ValueError, TypeError):
                LOGGER.error(
                    'Invalid type for `confidence` in course skills for course_key: %s', course['key']
                )
                failures.add((course['uuid'], course['key']))

        return failures

    def handle(self, *args, **options):
        """
        Entry point for management command execution.
        """
        if options['args_from_database']:
            options = self.get_args_from_database()

        self._refresh_skills(options)
