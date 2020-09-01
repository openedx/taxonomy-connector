"""
Management command for refreshing the skills associated with courses.
"""

import logging

from django.core.management.base import BaseCommand, CommandError
from taxonomy.emsi_client import EMSISkillsApiClient
from taxonomy.management.command_utils import get_mutually_exclusive_required_option, fetch_course_description
from taxonomy.models import CourseSkills, Skill

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    """
        Example usage:
            $ ./manage.py refresh_course_skills --all-courses --commit
            $ ./manage.py refresh_course_skills --course-id 'Course1' --course-id 'Course2' --commit
            $ ./manage.py refresh_course_skills --from-settings
        """
    help = 'Refreshes the skills associated with courses.'

    def add_arguments(self, parser):
        """
        Add arguments to the command parser.
        """
        parser.add_argument(
            '--course-id', '--course_id',
            dest='course_ids',
            action='append',
            help=u'Refreshes skills for the list of courses.'
        )
        parser.add_argument(
            '--all-courses', '--all', '--all_courses',
            dest='all_courses',
            action='store_true',
            default=False,
            help=u'Refreshes skills for all courses.'
        )
        parser.add_argument(
            '--from-settings', '--from_settings',
            dest='from_settings',
            help='Refreshes skills with settings set via django admin',
            action='store_true',
            default=False,
        )
        parser.add_argument(
            '--commit',
            dest='commit',
            action='store_true',
            default=False,
            help=u'Commits the skills to storage. '
        )

    def _get_options(self, options):
        """
        Returns the command arguments configured via django admin.
        """
        commit = options['commit']
        courses_mode = get_mutually_exclusive_required_option(options, 'course_ids', 'all_courses', 'from_settings')
        if courses_mode == 'all_courses':
            course_keys = [] #TODO
        elif courses_mode == 'course_ids':
            course_keys = options['course_ids']
        else:
            if self._latest_settings().all_courses:
                course_keys = [] #TODO
            else:
                course_keys = parse_course_keys(self._latest_settings().course_ids.split())
            commit = self._latest_settings().commit

        return course_keys, commit

    def _latest_settings(self):
        """
        Return the latest version of the RefreshSkillsSetting
        """
        return RefreshSkillsSetting.current() #TODO

    def _update_skills_data(self, course_key, confidence, skill_data):
        """
        Persist the skills data
        """
        skill, created = Skill.objects.update_or_create(**skill_data)
        course_skills = CourseSkills.objects.update_or_create(
            course_id=course_key,
            skill=skill,
            confidence=confidence
        )

    def _refresh_skills(self, course_keys, commit):
        """
        Refreshes the skills associated with the provided courses
        """
        client = EMSISkillsApiClient()
        for course_key in course_keys:
            course_description = fetch_course_description(course_key) #TODO
            if course_description:
                course_skills = client.get_course_skills(course_description)
                if course_skills:
                    for x in range(0, len(course_skills['data'])):
                        try:
                            confidence = float(course_skills['data'][x]['confidence'])
                            skill = course_skills['data'][x]['skill']
                            skill_data = {
                                'external_id': skill['id'],
                                'name': skill['name'],
                                'info_url': skill['infoUrl'],
                                'type_id': skill['type']['id'],
                                'type_name': skill['type']['name'],
                            }
                            if commit:
                                self._update_skills_data(course_key, confidence, skill_data)
                        except KeyError:
                            LOGGER.error('Missing keys in skills data for course_key:{}', course_key)

    def handle(self, *args, **options):
        """
        Entry point for management command execution.
        """
        course_keys, commit = self._get_options(options)
        self._refresh_skills(course_keys, commit)
