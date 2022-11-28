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

from taxonomy.exceptions import CourseMetadataNotFoundError, InvalidCommandOptionsError, TaxonomyAPIError
from taxonomy.models import CourseSkills, RefreshCourseSkillsConfig, Skill
from test_utils.mocks import MockCourse, mock_as_dict
from test_utils.providers import DiscoveryCourseMetadataProvider
from test_utils.sample_responses.skills import MISSING_NAME_SKILLS, SKILLS_EMSI_CLIENT_RESPONSE, TYPE_ERROR_SKILLS
from test_utils.testcase import TaxonomyTestCase


@mark.django_db
class RefreshCourseSkillsCommandTests(TaxonomyTestCase):
    """
    Test command `refresh_course_skills`.
    """
    command = 'refresh_course_skills'

    def setUp(self):
        super().setUp()
        self.skills_emsi_client_response = SKILLS_EMSI_CLIENT_RESPONSE
        self.missing_skills = MISSING_NAME_SKILLS
        self.type_error_skills = TYPE_ERROR_SKILLS
        self.course_1 = mock_as_dict(MockCourse())
        self.course_2 = mock_as_dict(MockCourse())
        self.course_3 = mock_as_dict(MockCourse())
        self.mock_access_token()

    def test_missing_arguments(self):
        """
        Test missing arguments.
        """
        with self.assertRaisesRegex(
                InvalidCommandOptionsError,
                'Either course, args_from_database or all argument must be provided.'
        ):
            call_command(self.command)

    def test_missing_arguments_from_database_config(self):
        """
        Test missing arguments from --args-from-database.
        """
        config = RefreshCourseSkillsConfig.get_solo()
        config.arguments = ''
        config.save()
        with self.assertRaisesRegex(InvalidCommandOptionsError, 'Either course or all argument must be provided.'):
            call_command(self.command, '--args-from-database')

    @responses.activate
    @mock.patch('taxonomy.management.commands.refresh_course_skills.get_course_metadata_provider')
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
    @mock.patch('taxonomy.management.commands.refresh_course_skills.get_course_metadata_provider')
    def test_course_without_description(self, get_course_provider_mock):
        """
        Test that command work as expected if course description does not exist.
        """
        self.course_1.title = ''
        self.course_1.short_description = ''
        self.course_1.full_description = ''
        get_course_provider_mock.return_value = DiscoveryCourseMetadataProvider([self.course_1])

        skill = Skill.objects.all()
        course_skill = CourseSkills.objects.all()
        self.assertEqual(skill.count(), 0)
        self.assertEqual(course_skill.count(), 0)

        with LogCapture(level=logging.INFO) as log_capture:
            call_command(self.command, '--course', self.course_1.uuid, '--commit')
            self.assertEqual(len(log_capture.records), 3)
            messages = [record.msg for record in log_capture.records]
            self.assertEqual(
                messages,
                [
                    '[TAXONOMY] Refresh Course Skills. Options: [%s]',
                    '[TAXONOMY] Refresh course skills process started.',
                    '[TAXONOMY] Refresh %s skills process completed. \n'
                    'Failures: %s \n'
                    'Total %s Updated Successfully: %s \n'
                    'Total %s Skipped: %s \n'
                    'Total Failures: %s \n'
                ]
            )

        self.assertEqual(skill.count(), 0)
        self.assertEqual(course_skill.count(), 0)

    @mock.patch('taxonomy.management.commands.refresh_course_skills.get_course_metadata_provider')
    @mock.patch('taxonomy.management.commands.refresh_course_skills.utils.EMSISkillsApiClient.get_product_skills')
    def test_course_skill_saved(self, get_product_skills_mock, get_course_provider_mock):
        """
        Test that the command creates a Skill and many CourseSkills records.
        """
        get_product_skills_mock.return_value = self.skills_emsi_client_response
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

    @mock.patch('taxonomy.management.commands.refresh_course_skills.get_course_metadata_provider')
    @mock.patch('taxonomy.management.commands.refresh_course_skills.utils.EMSISkillsApiClient.get_product_skills')
    def test_course_skill_saved_with_all_param(self, get_product_skills_mock, get_course_provider_mock):
        """
        Test that the command creates a Skill and many CourseSkills records using --all param.
        """
        get_product_skills_mock.return_value = self.skills_emsi_client_response
        get_course_provider_mock.return_value = DiscoveryCourseMetadataProvider(
            [self.course_1, self.course_2, self.course_3]
        )
        skill = Skill.objects.all()
        course_skill = CourseSkills.objects.all()
        self.assertEqual(skill.count(), 0)
        self.assertEqual(course_skill.count(), 0)

        call_command(self.command, '--all', '--commit')

        self.assertEqual(skill.count(), 4)
        self.assertEqual(course_skill.count(), 12)

    @responses.activate
    @mock.patch('taxonomy.management.commands.refresh_course_skills.get_course_metadata_provider')
    @mock.patch('taxonomy.management.commands.refresh_course_skills.utils.EMSISkillsApiClient.get_product_skills')
    @mock.patch('taxonomy.utils.get_translated_skill_attribute_val')
    def test_course_skill_not_saved_upon_exception(self,
                                                   mock_course_description,
                                                   get_product_skills_mock,
                                                   get_course_provider_mock):
        """
        Test that the command does not create any records when the API throws an exception.
        """
        mock_course_description.return_value = 'course description translation'
        get_product_skills_mock.side_effect = TaxonomyAPIError()
        get_course_provider_mock.return_value = DiscoveryCourseMetadataProvider(
            [self.course_1, self.course_2]
        )
        skill = Skill.objects.all()
        course_skill = CourseSkills.objects.all()
        self.assertEqual(skill.count(), 0)
        self.assertEqual(course_skill.count(), 0)

        with LogCapture(level=logging.INFO) as log_capture:
            call_command(self.command, '--course', self.course_1.uuid, '--course', self.course_2.uuid, '--commit')
            # Validate a descriptive and readable log message.
            self.assertEqual(len(log_capture.records), 5)
            messages = [record.msg for record in log_capture.records]
            self.assertEqual(
                messages,
                [
                    '[TAXONOMY] Refresh Course Skills. Options: [%s]',
                    '[TAXONOMY] Refresh course skills process started.',
                    '[TAXONOMY] API Error for key: {}'.format(self.course_1.key),
                    f'[TAXONOMY] API Error for key: {self.course_2.key}',
                    '[TAXONOMY] Refresh %s skills process completed. \n'
                    'Failures: %s \n'
                    'Total %s Updated Successfully: %s \n'
                    'Total %s Skipped: %s \n'
                    'Total Failures: %s \n'
                ]
            )

        self.assertEqual(skill.count(), 0)
        self.assertEqual(course_skill.count(), 0)

    @responses.activate
    @mock.patch('taxonomy.management.commands.refresh_course_skills.get_course_metadata_provider')
    @mock.patch('taxonomy.management.commands.refresh_course_skills.utils.EMSISkillsApiClient.get_product_skills')
    def test_args_from_database_config(self, get_product_skills_mock, get_course_provider_mock):
        """
        Test that the command works via args from database config.
        """
        config = RefreshCourseSkillsConfig.get_solo()
        config.arguments = ' --course {} --course {} --commit '.format(self.course_1.uuid, self.course_2.uuid)
        config.save()
        get_product_skills_mock.return_value = self.skills_emsi_client_response
        get_course_provider_mock.return_value = DiscoveryCourseMetadataProvider(
            [self.course_1, self.course_2],
        )
        skill = Skill.objects.all()
        course_skill = CourseSkills.objects.all()
        self.assertEqual(skill.count(), 0)
        self.assertEqual(course_skill.count(), 0)

        call_command(self.command, '--args-from-database')

        self.assertEqual(skill.count(), 4)
        for skill_details in self.skills_emsi_client_response['data']:
            assert Skill.objects.filter(
                name=skill_details['skill']['name'],
                description=skill_details['skill']['description'],
                type_id=skill_details['skill']['type']['id'],
                type_name=skill_details['skill']['type']['name'],
                info_url=skill_details['skill']['infoUrl'],
            ).exists()
        self.assertEqual(course_skill.count(), 8)

    @responses.activate
    @mock.patch('taxonomy.management.commands.refresh_course_skills.get_course_metadata_provider')
    @mock.patch('taxonomy.management.commands.refresh_course_skills.utils.EMSISkillsApiClient.get_product_skills')
    @mock.patch('taxonomy.utils.get_translated_skill_attribute_val')
    def test_course_skill_not_saved_for_key_error(
            self,
            mock_course_description,
            get_product_skills_mock,
            get_course_provider_mock
    ):
        """
        Test that the command does not create any records when a Skill key error occurs.
        """
        mock_course_description.return_value = 'course description translation'
        get_product_skills_mock.return_value = self.missing_skills
        get_course_provider_mock.return_value = DiscoveryCourseMetadataProvider(
            [self.course_1, self.course_2],
        )
        skill = Skill.objects.all()
        course_skill = CourseSkills.objects.all()
        self.assertEqual(skill.count(), 0)
        self.assertEqual(course_skill.count(), 0)

        with LogCapture(level=logging.INFO) as log_capture:
            call_command(self.command, '--course', self.course_1.uuid, '--course', self.course_2.uuid, '--commit')
            # Validate a descriptive and readable log message.
            self.assertEqual(len(log_capture.records), 7)
            messages = [record.msg for record in log_capture.records]
            self.assertEqual(
                messages,
                [
                    '[TAXONOMY] Refresh Course Skills. Options: [%s]',
                    '[TAXONOMY] Refresh course skills process started.',
                    f'[TAXONOMY] Missing keys in skills data for key: {self.course_1.key}',
                    '[TAXONOMY] Skills data received from EMSI. Skills: [%s]',
                    f'[TAXONOMY] Missing keys in skills data for key: {self.course_2.key}',
                    '[TAXONOMY] Skills data received from EMSI. Skills: [%s]',
                    '[TAXONOMY] Refresh %s skills process completed. \n'
                    'Failures: %s \n'
                    'Total %s Updated Successfully: %s \n'
                    'Total %s Skipped: %s \n'
                    'Total Failures: %s \n'
                ]
            )

        self.assertEqual(skill.count(), 0)
        self.assertEqual(course_skill.count(), 0)

    @responses.activate
    @mock.patch('taxonomy.management.commands.refresh_course_skills.get_course_metadata_provider')
    @mock.patch('taxonomy.management.commands.refresh_course_skills.utils.EMSISkillsApiClient.get_product_skills')
    @mock.patch('taxonomy.utils.get_translated_skill_attribute_val')
    def test_course_skill_not_saved_for_type_error(
            self,
            mock_course_description,
            get_product_skills_mock,
            get_course_provider_mock
    ):
        """
        Test that the command does not create any records when a record value error occurs.
        """
        mock_course_description.return_value = 'course description translation'
        get_product_skills_mock.return_value = self.type_error_skills
        get_course_provider_mock.return_value = DiscoveryCourseMetadataProvider(
            [self.course_1, self.course_2],
        )
        skill = Skill.objects.all()
        course_skill = CourseSkills.objects.all()
        self.assertEqual(skill.count(), 0)
        self.assertEqual(course_skill.count(), 0)

        with LogCapture(level=logging.INFO) as log_capture:
            call_command(self.command, '--course', self.course_1.uuid, '--course', self.course_2.uuid, '--commit')
            # Validate a descriptive and readable log message.
            self.assertEqual(len(log_capture.records), 7)
            messages = [record.msg for record in log_capture.records]
            self.assertEqual(
                messages,
                [
                    '[TAXONOMY] Refresh Course Skills. Options: [%s]',
                    '[TAXONOMY] Refresh course skills process started.',
                    f'[TAXONOMY] Invalid type for `confidence` in skills for key: {self.course_1.key}',
                    '[TAXONOMY] Skills data received from EMSI. Skills: [%s]',
                    f'[TAXONOMY] Invalid type for `confidence` in skills for key: {self.course_2.key}',
                    '[TAXONOMY] Skills data received from EMSI. Skills: [%s]',
                    '[TAXONOMY] Refresh %s skills process completed. \n'
                    'Failures: %s \n'
                    'Total %s Updated Successfully: %s \n'
                    'Total %s Skipped: %s \n'
                    'Total Failures: %s \n'
                ]
            )

        self.assertEqual(skill.count(), 0)
        self.assertEqual(course_skill.count(), 0)

    @responses.activate
    @mock.patch('taxonomy.management.commands.refresh_course_skills.get_course_metadata_provider')
    @mock.patch('taxonomy.management.commands.refresh_course_skills.utils.EMSISkillsApiClient.get_product_skills')
    @mock.patch('taxonomy.management.commands.refresh_course_skills.utils.process_skills_data')
    @mock.patch('taxonomy.utils.get_translated_skill_attribute_val')
    def test_course_skill_not_saved_for_exception(
            self,
            mock_course_description,
            mock_process_course_skills_data,
            get_product_skills_mock,
            get_course_provider_mock,

    ):
        """
        Test that the command does not create any records when a record value error occurs.
        """
        mock_course_description.return_value = 'course description translation'
        get_product_skills_mock.return_value = self.skills_emsi_client_response
        get_course_provider_mock.return_value = DiscoveryCourseMetadataProvider([self.course_1])
        mock_process_course_skills_data.side_effect = Exception("UNKNOWN ERROR.")
        skill = Skill.objects.all()
        course_skill = CourseSkills.objects.all()
        self.assertEqual(skill.count(), 0)
        self.assertEqual(course_skill.count(), 0)

        with LogCapture(level=logging.INFO) as log_capture:
            call_command(self.command, '--course', self.course_1.uuid, '--commit')
            # Validate a descriptive and readable log message.
            self.assertEqual(len(log_capture.records), 5)
            messages = [record.msg for record in log_capture.records]
            self.assertEqual(
                messages,
                ['[TAXONOMY] Refresh Course Skills. Options: [%s]',
                 '[TAXONOMY] Refresh course skills process started.',
                 '[TAXONOMY] Skills data received from EMSI. Skills: [%s]',
                 f'[TAXONOMY] Exception for key: {self.course_1.key} Error: UNKNOWN ERROR.',
                 '[TAXONOMY] Refresh %s skills process completed. \n'
                 'Failures: %s \n'
                 'Total %s Updated Successfully: %s \n'
                 'Total %s Skipped: %s \n'
                 'Total Failures: %s \n']
            )

        self.assertEqual(skill.count(), 0)
        self.assertEqual(course_skill.count(), 0)
