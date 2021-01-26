# -*- coding: utf-8 -*-
"""
Tests for the django management command `refresh_course_skills`.
"""

import logging
from uuid import uuid4

import mock
import responses
from pytest import mark
from testfixtures import LogCapture

from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils.translation import gettext as _

from taxonomy.exceptions import CourseMetadataNotFoundError, CourseSkillsRefreshError, TaxonomyAPIError
from taxonomy.models import CourseSkills, RefreshCourseSkillsConfig, Skill
from test_utils.mocks import MockCourse
from test_utils.providers import DiscoveryCourseMetadataProvider
from test_utils.sample_responses.skills import MISSING_NAME_SKILLS, SKILLS, TYPE_ERROR_SKILLS
from test_utils.testcase import TaxonomyTestCase


@mark.django_db
class RefreshCourseSkillsCommandTests(TaxonomyTestCase):
    """
    Test command `refresh_course_skills`.
    """
    command = 'refresh_course_skills'

    def setUp(self):
        super().setUp()
        self.skills = SKILLS
        self.missing_skills = MISSING_NAME_SKILLS
        self.type_error_skills = TYPE_ERROR_SKILLS
        self.course_1 = MockCourse()
        self.course_2 = MockCourse()
        self.course_3 = MockCourse()
        self.mock_access_token()

    def test_missing_arguments(self):
        """
        Test missing arguments.
        """
        with self.assertRaisesRegex(CommandError, 'Either course or args_from_database argument must be present'):
            call_command(self.command)

    @responses.activate
    @mock.patch('taxonomy.management.commands.refresh_course_skills.utils.get_course_metadata_provider')
    def test_non_existant_course(self, get_course_provider_mock):
        """
        Test that command work as expected if course does not exist for a course uuid.
        """
        course_uuid = str(uuid4())
        get_course_provider_mock.return_value = DiscoveryCourseMetadataProvider([])

        with self.assertRaises(CourseMetadataNotFoundError) as assert_context:
            call_command(self.command, '--course', course_uuid)

        self.assertEqual(
            assert_context.exception.args[0],
            'No course metadata was found for following courses. {}'.format([course_uuid])
        )

    @responses.activate
    @mock.patch('taxonomy.management.commands.refresh_course_skills.utils.get_course_metadata_provider')
    @mock.patch('taxonomy.management.commands.refresh_course_skills.utils.EMSISkillsApiClient.get_course_skills')
    def test_course_skill_saved(self, get_course_skills_mock, get_course_provider_mock):
        """
        Test that the command creates a Skill and many CourseSkills records.
        """
        get_course_skills_mock.return_value = self.skills
        get_course_provider_mock.return_value = DiscoveryCourseMetadataProvider(
            [self.course_1, self.course_2]
        )
        skill = Skill.objects.all()
        course_skill = CourseSkills.objects.all()
        self.assertEqual(skill.count(), 0)
        self.assertEqual(course_skill.count(), 0)

        call_command(self.command, '--course', self.course_1.uuid, '--course', self.course_2.uuid, '--commit')

        self.assertEqual(skill.count(), 4)
        self.assertEqual(course_skill.count(), 8)

        call_command(self.command, '--course', self.course_1.uuid, '--course', self.course_2.uuid, '--commit')

        self.assertEqual(skill.count(), 4)
        self.assertEqual(course_skill.count(), 8)

        get_course_provider_mock.return_value = DiscoveryCourseMetadataProvider(
            [self.course_3, self.course_1]
        )
        call_command(self.command, '--course', self.course_3.uuid, '--course', self.course_1.uuid, '--commit')

        self.assertEqual(skill.count(), 4)
        self.assertEqual(course_skill.count(), 12)

    @responses.activate
    @mock.patch('taxonomy.management.commands.refresh_course_skills.utils.EMSISkillsApiClient.get_course_skills')
    def test_course_skill_not_saved_upon_exception(self, get_course_skills_mock):
        """
        Test that the command does not create any records when the API throws an exception.
        """
        get_course_skills_mock.side_effect = TaxonomyAPIError()
        skill = Skill.objects.all()
        course_skill = CourseSkills.objects.all()
        self.assertEqual(skill.count(), 0)
        self.assertEqual(course_skill.count(), 0)

        err_string = _('Could not refresh skills for the following courses:.*')
        with LogCapture(level=logging.INFO) as log_capture:
            with self.assertRaisesRegex(CourseSkillsRefreshError, err_string):
                call_command(self.command, '--course', self.course_1.uuid, '--course', self.course_2.uuid, '--commit')
            # Validate a descriptive and readable log message.
            self.assertEqual(len(log_capture.records), 2)
            message = log_capture.records[0].msg
            self.assertEqual(message, '[TAXONOMY] API Error for course_key: %s')

        self.assertEqual(skill.count(), 0)
        self.assertEqual(course_skill.count(), 0)

    @responses.activate
    @mock.patch('taxonomy.management.commands.refresh_course_skills.utils.get_course_metadata_provider')
    @mock.patch('taxonomy.management.commands.refresh_course_skills.utils.EMSISkillsApiClient.get_course_skills')
    def test_args_from_database_config(self, get_course_skills_mock, get_course_provider_mock):
        """
        Test that the command works via args from database config.
        """
        config = RefreshCourseSkillsConfig.get_solo()
        config.arguments = ' --course {} --course {} --commit '.format(self.course_1.uuid, self.course_2.uuid)
        config.save()
        get_course_skills_mock.return_value = self.skills
        get_course_provider_mock.return_value = DiscoveryCourseMetadataProvider(
            [self.course_1, self.course_2],
        )
        skill = Skill.objects.all()
        course_skill = CourseSkills.objects.all()
        self.assertEqual(skill.count(), 0)
        self.assertEqual(course_skill.count(), 0)

        call_command(self.command, '--args-from-database')

        self.assertEqual(skill.count(), 4)
        self.assertEqual(course_skill.count(), 8)

    @responses.activate
    @mock.patch('taxonomy.management.commands.refresh_course_skills.utils.get_course_metadata_provider')
    @mock.patch('taxonomy.management.commands.refresh_course_skills.utils.EMSISkillsApiClient.get_course_skills')
    def test_course_skill_not_saved_for_key_error(self, get_course_skills_mock, get_course_provider_mock):
        """
        Test that the command does not create any records when a Skill key error occurs.
        """
        get_course_skills_mock.return_value = self.missing_skills
        get_course_provider_mock.return_value = DiscoveryCourseMetadataProvider(
            [self.course_1, self.course_2],
        )
        skill = Skill.objects.all()
        course_skill = CourseSkills.objects.all()
        self.assertEqual(skill.count(), 0)
        self.assertEqual(course_skill.count(), 0)

        err_string = _('Could not refresh skills for the following courses:.*')
        with LogCapture(level=logging.INFO) as log_capture:
            with self.assertRaisesRegex(CourseSkillsRefreshError, err_string):
                call_command(self.command, '--course', self.course_1.uuid, '--course', self.course_2.uuid, '--commit')
            # Validate a descriptive and readable log message.
            self.assertEqual(len(log_capture.records), 2)
            message = log_capture.records[0].msg
            self.assertEqual(message, '[TAXONOMY] Missing keys in skills data for course_key: %s')

        self.assertEqual(skill.count(), 0)
        self.assertEqual(course_skill.count(), 0)

    @responses.activate
    @mock.patch('taxonomy.management.commands.refresh_course_skills.utils.get_course_metadata_provider')
    @mock.patch('taxonomy.management.commands.refresh_course_skills.utils.EMSISkillsApiClient.get_course_skills')
    def test_course_skill_not_saved_for_type_error(self, get_course_skills_mock, get_course_provider_mock):
        """
        Test that the command does not create any records when a record value error occurs.
        """
        get_course_skills_mock.return_value = self.type_error_skills
        get_course_provider_mock.return_value = DiscoveryCourseMetadataProvider(
            [self.course_1, self.course_2],
        )
        skill = Skill.objects.all()
        course_skill = CourseSkills.objects.all()
        self.assertEqual(skill.count(), 0)
        self.assertEqual(course_skill.count(), 0)

        err_string = _('Could not refresh skills for the following courses:.*')
        with LogCapture(level=logging.INFO) as log_capture:
            with self.assertRaisesRegex(CourseSkillsRefreshError, err_string):
                call_command(self.command, '--course', self.course_1.uuid, '--course', self.course_2.uuid, '--commit')
            # Validate a descriptive and readable log message.
            self.assertEqual(len(log_capture.records), 2)
            message = log_capture.records[0].msg
            self.assertEqual(message, '[TAXONOMY] Invalid type for `confidence` in course skills for course_key: %s')

        self.assertEqual(skill.count(), 0)
        self.assertEqual(course_skill.count(), 0)
