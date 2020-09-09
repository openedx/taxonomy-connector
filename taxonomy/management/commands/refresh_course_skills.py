"""
Management command for refreshing the skills associated with courses.
"""

import logging

from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import gettext as _

from taxonomy.emsi_client import EMSISkillsApiClient
from taxonomy.models import CourseSkills, Skill, RefreshCourseSkillsConfig
from taxonomy.exceptions import TaxonomyServiceAPIError
from taxonomy.api_client.discovery import get_courses, extract_course_description


LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    """
        Example usage:
            $ ./manage.py refresh_course_skills --course 'Course1' --course 'Course2' --commit
            $ ./manage.py refresh_course_skills --args-from-database
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
        skill, created = Skill.objects.update_or_create(**skill_data)
        CourseSkills.objects.update_or_create(
            course_id=course_key,
            skill=skill,
            confidence=confidence
        )

    def _refresh_skills(self, options):
        """
        Refreshes the skills associated with the provided courses
        """
        courses = get_courses(options)

        if not courses:
            raise CommandError(_('No courses found. Did you specify an argument?'))

        failures = set()
        client = EMSISkillsApiClient()
        for course in courses:
            course_description = extract_course_description(course)
            if course_description:
                try:
                    course_skills = client.get_course_skills(course_description)
                except TaxonomyServiceAPIError:
                    LOGGER.error('Taxonomy Service Error for course_key:{}', course.key)
                    failures.add(course)
                else:
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
                            if options['commit']:
                                self._update_skills_data(course.key, confidence, skill_data)
                        except KeyError:
                            LOGGER.error('Missing keys in skills data for course_key: {}', course.key)
                            failures.add(course)
                        except (ValueError, TypeError):
                            LOGGER.error(
                                'Invalid type for `confidence` in course skills for course_key: {}', course.key
                            )
                            failures.add(course)
        if failures:
            keys = sorted('{key} ({id})'.format(key=failure.key, id=failure.id) for failure in failures)
            raise CommandError(
                _('Could not refresh skills for the following courses: {course_keys}').format(
                    course_keys=', '.join(keys)
                )
            )

    def handle(self, *args, **options):
        """
        Entry point for management command execution.
        """
        if options['args_from_database']:
            options = self.get_args_from_database()

        self._refresh_skills(options)
