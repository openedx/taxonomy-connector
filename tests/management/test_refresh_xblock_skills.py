# -*- coding: utf-8 -*-
"""
Tests for the django management command `refresh_xblock_skills`.
"""

import logging
from uuid import uuid4

import mock
import responses
from pytest import mark
from testfixtures import LogCapture

from django.core.management import call_command

from taxonomy.exceptions import InvalidCommandOptionsError, TaxonomyAPIError, XBlockMetadataNotFoundError
from taxonomy.models import (
    CourseRunXBlockSkillsTracker,
    Skill,
    RefreshXBlockSkillsConfig,
    XBlockSkillData,
    XBlockSkills
)
from test_utils.mocks import MockCourseRun, MockXBlock, mock_as_dict
from test_utils.providers import DiscoveryCourseRunMetadataProvider, DiscoveryXBlockMetadataProvider
from test_utils.sample_responses.skills import MISSING_NAME_SKILLS, SKILLS_EMSI_CLIENT_RESPONSE, TYPE_ERROR_SKILLS
from test_utils.testcase import TaxonomyTestCase


@mark.django_db
class RefreshXBlockSkillsCommandTests(TaxonomyTestCase):
    """
    Test command `refresh_xblock_skills`.
    """
    command = 'refresh_xblock_skills'

    def setUp(self):
        super().setUp()
        self.skills_emsi_client_response = SKILLS_EMSI_CLIENT_RESPONSE
        self.missing_skills = MISSING_NAME_SKILLS
        self.type_error_skills = TYPE_ERROR_SKILLS
        self.course_1 = mock_as_dict(MockCourseRun())
        self.course_2 = mock_as_dict(MockCourseRun())
        self.course_3 = mock_as_dict(MockCourseRun())
        self.xblock_1 = mock_as_dict(MockXBlock())
        self.xblock_2 = mock_as_dict(MockXBlock())
        self.xblock_3 = mock_as_dict(MockXBlock())
        self.mock_access_token()

    def assert_xblock_skill_count(self, skill_count, xblock_skill_count, xblock_skill_data_count):
        """
        Asserts that the number of skills, xblock skills, and xblock skill data
        objects in the database are as expected.

        Args:
            skill_count (int): The expected number of skills in the database.
            xblock_skill_count (int): The expected number of xblock skills in the database.
            xblock_skill_data_count (int): The expected number of xblock skill data in the database.
        """
        self.assertEqual(Skill.objects.count(), skill_count)
        self.assertEqual(XBlockSkills.objects.count(), xblock_skill_count)
        self.assertEqual(XBlockSkillData.objects.count(), xblock_skill_data_count)

    def test_missing_arguments(self):
        """
        Test missing arguments.
        """
        with self.assertRaisesRegex(
                InvalidCommandOptionsError,
                'Either course, xblock, args_from_database or all argument must be provided.'
        ):
            call_command(self.command)

    def test_missing_arguments_from_database_config(self):
        """
        Test missing arguments from --args-from-database.
        """
        config = RefreshXBlockSkillsConfig.get_solo()
        config.arguments = ''
        config.save()
        with self.assertRaisesRegex(
                InvalidCommandOptionsError,
                'Either course, xblock or --all argument must be provided.',
        ):
            call_command(self.command, '--args-from-database')

    def test_course_and_xblock_argument_raise_error(self):
        """
        Test that the command raises an error with both course and xblock arguments.
        """
        with self.assertRaises(InvalidCommandOptionsError) as assert_context:
            call_command(self.command, '--course', self.course_1.course_key, '--xblock', self.xblock_2.key)
            self.assertEqual(
                assert_context.exception.args[0],
                'Either course or xblock argument should be provided and not both.'
            )

    @responses.activate
    @mock.patch('taxonomy.management.commands.refresh_xblock_skills.get_xblock_metadata_provider')
    def test_non_existant_xblock(self, get_xblock_metadata_provider):
        """
        Test that command throws XBlockMetadataNotFoundError if xblock does not
        exist for a xblock key.
        """
        xblock_key = str(uuid4())
        get_xblock_metadata_provider.return_value = DiscoveryXBlockMetadataProvider([])

        with self.assertRaises(XBlockMetadataNotFoundError) as assert_context:
            call_command(self.command, '--xblock', xblock_key)
            self.assertEqual(
                assert_context.exception.args[0],
                'No xblock metadata was found for following xblocks. {}'.format([xblock_key])
            )

    @responses.activate
    @mock.patch('taxonomy.management.commands.refresh_xblock_skills.get_xblock_metadata_provider')
    def test_xblock_without_content(self, get_xblock_metadata_provider):
        """
        Test that command work as expected if xblock content does not exist.
        """
        self.xblock_1.content = ''
        get_xblock_metadata_provider.return_value = DiscoveryXBlockMetadataProvider([self.xblock_1])

        self.assert_xblock_skill_count(0, 0, 0)

        with LogCapture(level=logging.INFO) as log_capture:
            call_command(self.command, '--xblock', self.xblock_1.key, '--commit')
            self.assertEqual(len(log_capture.records), 3)
            messages = [record.msg for record in log_capture.records]
            self.assertEqual(
                messages,
                [
                    '[TAXONOMY] Refresh XBlock Skills. Options: [%s]',
                    '[TAXONOMY] Refresh XBlock skills process started for xblocks: [%s]',
                    '[TAXONOMY] Refresh %s skills process completed. \n'
                    'Failures: %s \n'
                    'Total %s Updated Successfully: %s \n'
                    'Total %s Skipped: %s \n'
                    'Total Failures: %s \n'
                ]
            )

        self.assert_xblock_skill_count(0, 0, 0)

    @responses.activate
    @mock.patch('taxonomy.management.commands.refresh_xblock_skills.get_xblock_metadata_provider')
    @mock.patch('taxonomy.management.commands.refresh_xblock_skills.get_course_run_metadata_provider')
    def test_missing_course_key_with_all(self, get_course_run_metadata_provider, get_xblock_metadata_provider):
        """
        Test that command logs error and skips processing for it if course key is missing.
        """
        self.course_1.course_key = None
        get_course_run_metadata_provider.return_value = DiscoveryCourseRunMetadataProvider([self.course_1])
        get_xblock_metadata_provider.return_value = DiscoveryXBlockMetadataProvider([self.xblock_1])

        self.assert_xblock_skill_count(0, 0, 0)

        with LogCapture(level=logging.INFO) as log_capture:
            call_command(self.command, '--all', '--commit')
            messages = [record.msg for record in log_capture.records]
            # self.assertEqual(len(log_capture.records), 2)
            self.assertEqual(
                messages,
                [
                    '[TAXONOMY] Refresh XBlock Skills. Options: [%s]',
                    '[TAXONOMY] Invalid %s: [%s]',
                ]
            )

        self.assert_xblock_skill_count(0, 0, 0)

    @mock.patch('taxonomy.management.commands.refresh_xblock_skills.get_xblock_metadata_provider')
    @mock.patch('taxonomy.management.commands.refresh_xblock_skills.utils.EMSISkillsApiClient.get_product_skills')
    def test_course_xblock_skills_saved(self, get_product_skills_mock, get_xblock_provider_mock):
        """
        Test that the command creates a Skill and many XBlockSkillData records.
        """
        get_product_skills_mock.return_value = self.skills_emsi_client_response
        get_xblock_provider_mock.return_value = DiscoveryXBlockMetadataProvider(block_count=1)
        self.assert_xblock_skill_count(0, 0, 0)

        call_command(
            self.command,
            '--course',
            self.course_1.course_key,
            '--course',
            self.course_2.course_key,
            '--commit'
        )

        self.assert_xblock_skill_count(4, 2, 8)
        self.assertEqual(CourseRunXBlockSkillsTracker.objects.count(), 2)

        call_command(
            self.command,
            '--course',
            self.course_3.course_key,
            '--course',
            self.course_1.course_key,
            '--commit'
        )

        self.assert_xblock_skill_count(4, 3, 12)
        self.assertEqual(CourseRunXBlockSkillsTracker.objects.count(), 3)

    @mock.patch('taxonomy.management.commands.refresh_xblock_skills.get_xblock_metadata_provider')
    @mock.patch('taxonomy.management.commands.refresh_xblock_skills.get_course_run_metadata_provider')
    @mock.patch('taxonomy.management.commands.refresh_xblock_skills.utils.EMSISkillsApiClient.get_product_skills')
    def test_course_xblock_skill_saved_with_all_param(
            self,
            get_product_skills_mock,
            get_course_run_provider_mock,
            get_xblock_provider_mock,
    ):
        """
        Test that the command creates a Skill and many XBlockSkillData records using --all param.
        """
        get_product_skills_mock.return_value = self.skills_emsi_client_response
        get_course_run_provider_mock.return_value = DiscoveryCourseRunMetadataProvider(
            [self.course_1, self.course_2, self.course_3]
        )
        get_xblock_provider_mock.return_value = DiscoveryXBlockMetadataProvider(block_count=1)
        self.assert_xblock_skill_count(0, 0, 0)

        call_command(self.command, '--all', '--commit')

        self.assert_xblock_skill_count(4, 3, 12)
        self.assertEqual(CourseRunXBlockSkillsTracker.objects.count(), 3)

    @mock.patch('taxonomy.management.commands.refresh_xblock_skills.get_xblock_metadata_provider')
    @mock.patch('taxonomy.management.commands.refresh_xblock_skills.get_course_run_metadata_provider')
    @mock.patch('taxonomy.management.commands.refresh_xblock_skills.utils.EMSISkillsApiClient.get_product_skills')
    def test_course_xblock_skill_not_marked_complete_if_success_ratio_less_than_threshold(
            self,
            get_product_skills_mock,
            get_course_run_provider_mock,
            get_xblock_provider_mock,
    ):
        """
        Test that the command does not mark course as complete if success_ratio is less than threshold.
        """
        get_product_skills_mock.side_effect = TaxonomyAPIError()
        get_course_run_provider_mock.return_value = DiscoveryCourseRunMetadataProvider([self.course_1])
        get_xblock_provider_mock.return_value = DiscoveryXBlockMetadataProvider(block_count=4)
        self.assert_xblock_skill_count(0, 0, 0)

        call_command(self.command, '--all', '--commit')

        self.assertEqual(CourseRunXBlockSkillsTracker.objects.count(), 0)

    @responses.activate
    @mock.patch('taxonomy.management.commands.refresh_xblock_skills.get_xblock_metadata_provider')
    @mock.patch('taxonomy.management.commands.refresh_xblock_skills.utils.EMSISkillsApiClient.get_product_skills')
    def test_xblock_skill_not_saved_upon_exception(self,
                                                   get_product_skills_mock,
                                                   get_xblock_provider_mock):
        """
        Test that the command does not create any records when the API throws an exception.
        """
        get_product_skills_mock.side_effect = TaxonomyAPIError()
        get_xblock_provider_mock.return_value = DiscoveryXBlockMetadataProvider(
            [self.xblock_1, self.xblock_2]
        )
        self.assert_xblock_skill_count(0, 0, 0)

        with LogCapture(level=logging.INFO) as log_capture:
            call_command(self.command, '--xblock', self.xblock_1.key, '--xblock', self.xblock_2.key, '--commit')
            # Validate a descriptive and readable log message.
            self.assertEqual(len(log_capture.records), 5)
            messages = [record.msg for record in log_capture.records]
            self.assertEqual(
                messages,
                [
                    '[TAXONOMY] Refresh XBlock Skills. Options: [%s]',
                    '[TAXONOMY] Refresh XBlock skills process started for xblocks: [%s]',
                    '[TAXONOMY] API Error for key: {}'.format(self.xblock_1.key),
                    '[TAXONOMY] API Error for key: {}'.format(self.xblock_2.key),
                    '[TAXONOMY] Refresh %s skills process completed. \n'
                    'Failures: %s \n'
                    'Total %s Updated Successfully: %s \n'
                    'Total %s Skipped: %s \n'
                    'Total Failures: %s \n'
                ]
            )

        self.assert_xblock_skill_count(0, 0, 0)

    @responses.activate
    @mock.patch('taxonomy.management.commands.refresh_xblock_skills.get_xblock_metadata_provider')
    @mock.patch('taxonomy.management.commands.refresh_xblock_skills.utils.EMSISkillsApiClient.get_product_skills')
    def test_args_from_database_config(self, get_product_skills_mock, get_xblock_provider_mock):
        """
        Test that the command works via args from database config.
        """
        config = RefreshXBlockSkillsConfig.get_solo()
        config.arguments = ' --xblock {} --xblock {} --commit '.format(self.xblock_1.key, self.xblock_2.key)
        config.save()
        get_product_skills_mock.return_value = self.skills_emsi_client_response
        get_xblock_provider_mock.return_value = DiscoveryXBlockMetadataProvider(
            [self.xblock_1, self.xblock_2],
        )
        self.assert_xblock_skill_count(0, 0, 0)

        call_command(self.command, '--args-from-database')

        self.assert_xblock_skill_count(4, 2, 8)
        for skill_details in self.skills_emsi_client_response['data']:
            assert Skill.objects.filter(
                name=skill_details['skill']['name'],
                description=skill_details['skill']['description'],
                type_id=skill_details['skill']['type']['id'],
                type_name=skill_details['skill']['type']['name'],
                info_url=skill_details['skill']['infoUrl'],
            ).exists()

    @responses.activate
    @mock.patch('taxonomy.management.commands.refresh_xblock_skills.get_xblock_metadata_provider')
    @mock.patch('taxonomy.management.commands.refresh_xblock_skills.utils.EMSISkillsApiClient.get_product_skills')
    def test_xblock_skill_not_saved_for_key_error(
            self,
            get_product_skills_mock,
            get_xblock_provider_mock
    ):
        """
        Test that the command does not create any records when a Skill key error occurs.
        """
        get_product_skills_mock.return_value = self.missing_skills
        get_xblock_provider_mock.return_value = DiscoveryXBlockMetadataProvider(
            [self.xblock_1, self.xblock_2],
        )
        self.assert_xblock_skill_count(0, 0, 0)

        with LogCapture(level=logging.INFO) as log_capture:
            call_command(self.command, '--xblock', self.xblock_1.key, '--xblock', self.xblock_2.key, '--commit')
            # Validate a descriptive and readable log message.
            messages = [record.msg for record in log_capture.records]
            self.assertEqual(len(log_capture.records), 7)
            self.assertEqual(
                messages,
                [
                    '[TAXONOMY] Refresh XBlock Skills. Options: [%s]',
                    '[TAXONOMY] Refresh XBlock skills process started for xblocks: [%s]',
                    f'[TAXONOMY] Missing keys in skills data for key: {self.xblock_1.key}',
                    '[TAXONOMY] Skills data received from EMSI. Skills: [%s]',
                    f'[TAXONOMY] Missing keys in skills data for key: {self.xblock_2.key}',
                    '[TAXONOMY] Skills data received from EMSI. Skills: [%s]',
                    '[TAXONOMY] Refresh %s skills process completed. \n'
                    'Failures: %s \n'
                    'Total %s Updated Successfully: %s \n'
                    'Total %s Skipped: %s \n'
                    'Total Failures: %s \n'
                ]
            )

        self.assert_xblock_skill_count(0, 0, 0)

    @responses.activate
    @mock.patch('taxonomy.management.commands.refresh_xblock_skills.get_xblock_metadata_provider')
    @mock.patch('taxonomy.management.commands.refresh_xblock_skills.utils.EMSISkillsApiClient.get_product_skills')
    def test_xblock_skill_not_saved_for_type_error(
            self,
            get_product_skills_mock,
            get_xblock_provider_mock
    ):
        """
        Test that the command does not create any records when a record value error occurs.
        """
        get_product_skills_mock.return_value = self.type_error_skills
        get_xblock_provider_mock.return_value = DiscoveryXBlockMetadataProvider(
            [self.xblock_1, self.xblock_2],
        )
        self.assert_xblock_skill_count(0, 0, 0)

        with LogCapture(level=logging.INFO) as log_capture:
            call_command(self.command, '--xblock', self.xblock_1.key, '--xblock', self.xblock_2.key, '--commit')
            # Validate a descriptive and readable log message.
            self.assertEqual(len(log_capture.records), 7)
            messages = [record.msg for record in log_capture.records]
            self.assertEqual(
                messages,
                [
                    '[TAXONOMY] Refresh XBlock Skills. Options: [%s]',
                    '[TAXONOMY] Refresh XBlock skills process started for xblocks: [%s]',
                    f'[TAXONOMY] Invalid type for `confidence` in skills for key: {self.xblock_1.key}',
                    '[TAXONOMY] Skills data received from EMSI. Skills: [%s]',
                    f'[TAXONOMY] Invalid type for `confidence` in skills for key: {self.xblock_2.key}',
                    '[TAXONOMY] Skills data received from EMSI. Skills: [%s]',
                    '[TAXONOMY] Refresh %s skills process completed. \n'
                    'Failures: %s \n'
                    'Total %s Updated Successfully: %s \n'
                    'Total %s Skipped: %s \n'
                    'Total Failures: %s \n'
                ]
            )

        self.assert_xblock_skill_count(0, 0, 0)

    @responses.activate
    @mock.patch('taxonomy.management.commands.refresh_xblock_skills.get_xblock_metadata_provider')
    @mock.patch('taxonomy.management.commands.refresh_xblock_skills.utils.EMSISkillsApiClient.get_product_skills')
    @mock.patch('taxonomy.management.commands.refresh_xblock_skills.utils.process_skills_data')
    def test_xblock_skill_not_saved_for_exception(
            self,
            mock_process_xblock_skills_data,
            get_product_skills_mock,
            get_xblock_provider_mock,

    ):
        """
        Test that the command does not create any records when a record value error occurs.
        """
        get_product_skills_mock.return_value = self.skills_emsi_client_response
        get_xblock_provider_mock.return_value = DiscoveryXBlockMetadataProvider([self.xblock_1])
        mock_process_xblock_skills_data.side_effect = Exception("UNKNOWN ERROR.")
        self.assert_xblock_skill_count(0, 0, 0)

        with LogCapture(level=logging.INFO) as log_capture:
            call_command(self.command, '--xblock', self.xblock_1.key, '--commit')
            # Validate a descriptive and readable log message.
            self.assertEqual(len(log_capture.records), 5)
            messages = [record.msg for record in log_capture.records]
            self.assertEqual(
                messages,
                ['[TAXONOMY] Refresh XBlock Skills. Options: [%s]',
                 '[TAXONOMY] Refresh XBlock skills process started for xblocks: [%s]',
                 '[TAXONOMY] Skills data received from EMSI. Skills: [%s]',
                 f'[TAXONOMY] Exception for key: {self.xblock_1.key} Error: UNKNOWN ERROR.',
                 '[TAXONOMY] Refresh %s skills process completed. \n'
                 'Failures: %s \n'
                 'Total %s Updated Successfully: %s \n'
                 'Total %s Skipped: %s \n'
                 'Total Failures: %s \n']
            )

        self.assert_xblock_skill_count(0, 0, 0)
