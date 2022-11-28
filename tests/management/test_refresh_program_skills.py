# -*- coding: utf-8 -*-
"""
Tests for the django management command `refresh_program_skills`.
"""

import logging
from uuid import uuid4

import mock
import responses
from pytest import mark
from testfixtures import LogCapture

from django.core.management import call_command

from taxonomy.exceptions import ProgramMetadataNotFoundError, InvalidCommandOptionsError, TaxonomyAPIError
from taxonomy.models import ProgramSkill, RefreshProgramSkillsConfig, Skill
from test_utils.mocks import MockProgram, mock_as_dict
from test_utils.providers import DiscoveryProgramMetadataProvider
from test_utils.sample_responses.skills import MISSING_NAME_SKILLS, SKILLS_EMSI_CLIENT_RESPONSE, TYPE_ERROR_SKILLS
from test_utils.testcase import TaxonomyTestCase


@mark.django_db
class RefreshProgramSkillsCommandTests(TaxonomyTestCase):
    """
    Test command `refresh_program_skills`.
    """
    command = 'refresh_program_skills'

    def setUp(self):
        super().setUp()
        self.skills_emsi_client_response = SKILLS_EMSI_CLIENT_RESPONSE
        self.missing_skills = MISSING_NAME_SKILLS
        self.type_error_skills = TYPE_ERROR_SKILLS
        self.program_1 = mock_as_dict(MockProgram())
        self.program_2 = mock_as_dict(MockProgram())
        self.program_3 = mock_as_dict(MockProgram())
        self.mock_access_token()

    def test_missing_arguments(self):
        """
        Test missing arguments.
        """
        with self.assertRaisesRegex(
                InvalidCommandOptionsError,
                'Either program, args_from_database or all argument must be provided.'
        ):
            call_command(self.command)

    def test_missing_arguments_from_database_config(self):
        """
        Test missing arguments from --args-from-database.
        """
        config = RefreshProgramSkillsConfig.get_solo()
        config.arguments = ''
        config.save()
        with self.assertRaisesRegex(InvalidCommandOptionsError, 'Either program or all argument must be provided.'):
            call_command(self.command, '--args-from-database')

    @responses.activate
    @mock.patch('taxonomy.management.commands.refresh_program_skills.get_program_metadata_provider')
    def test_non_existant_program(self, get_program_provider_mock):
        """
        Test that command work as expected if program does not exist for a program uuid.
        """
        program_uuid = str(uuid4())
        get_program_provider_mock.return_value = DiscoveryProgramMetadataProvider([])

        with self.assertRaises(ProgramMetadataNotFoundError) as assert_context:
            call_command(self.command, '--program', program_uuid)

        self.assertEqual(
            assert_context.exception.args[0],
            'No program metadata was found for following programs. {}'.format([program_uuid])
        )

    @responses.activate
    @mock.patch('taxonomy.management.commands.refresh_program_skills.get_program_metadata_provider')
    def test_program_without_overview(self, get_program_provider_mock):
        """
        Test that command work as expected if program overview does not exist.
        """
        self.program_1.overview = ''
        get_program_provider_mock.return_value = DiscoveryProgramMetadataProvider([self.program_1])

        skill = Skill.objects.all()
        program_skill = ProgramSkill.objects.all()
        self.assertEqual(skill.count(), 0)
        self.assertEqual(program_skill.count(), 0)

        with LogCapture(level=logging.INFO) as log_capture:
            call_command(self.command, '--program', self.program_1.uuid, '--commit')
            self.assertEqual(len(log_capture.records), 3)
            messages = [record.msg for record in log_capture.records]
            self.assertEqual(
                messages,
                [
                    '[TAXONOMY] Refresh Program Skills. Options: [%s]',
                    '[TAXONOMY] Refresh program skills process started.',
                    '[TAXONOMY] Refresh %s skills process completed. \n'
                    'Failures: %s \n'
                    'Total %s Updated Successfully: %s \n'
                    'Total %s Skipped: %s \n'
                    'Total Failures: %s \n'
                ]
            )

        self.assertEqual(skill.count(), 0)
        self.assertEqual(program_skill.count(), 0)

    @mock.patch('taxonomy.management.commands.refresh_program_skills.get_program_metadata_provider')
    @mock.patch('taxonomy.management.commands.refresh_course_skills.utils.EMSISkillsApiClient.get_product_skills')
    def test_program_skill_saved(self, get_product_skills_mock, get_program_provider_mock):
        """
        Test that the command creates a Skill and many ProgramSkill records.
        """
        get_product_skills_mock.return_value = self.skills_emsi_client_response
        get_program_provider_mock.return_value = DiscoveryProgramMetadataProvider(
            [self.program_1, self.program_2]
        )
        skill = Skill.objects.all()
        program_skill = ProgramSkill.objects.all()
        self.assertEqual(skill.count(), 0)
        self.assertEqual(program_skill.count(), 0)

        call_command(self.command, '--program', self.program_1.uuid, '--program', self.program_2.uuid, '--commit')

        self.assertEqual(skill.count(), 4)
        self.assertEqual(program_skill.count(), 8)

        call_command(self.command, '--program', self.program_1.uuid, '--program', self.program_2.uuid, '--commit')

        self.assertEqual(skill.count(), 4)
        self.assertEqual(program_skill.count(), 8)

        get_program_provider_mock.return_value = DiscoveryProgramMetadataProvider(
            [self.program_3, self.program_1]
        )
        call_command(self.command, '--program', self.program_3.uuid, '--program', self.program_1.uuid, '--commit')

        self.assertEqual(skill.count(), 4)
        self.assertEqual(program_skill.count(), 12)

    @mock.patch('taxonomy.management.commands.refresh_program_skills.get_program_metadata_provider')
    @mock.patch('taxonomy.management.commands.refresh_course_skills.utils.EMSISkillsApiClient.get_product_skills')
    def test_course_skill_saved_with_all_param(self, get_product_skills_mock, get_program_provider_mock):
        """
        Test that the command creates a Skill and many ProgramSkill records using --all param.
        """
        get_product_skills_mock.return_value = self.skills_emsi_client_response
        get_program_provider_mock.return_value = DiscoveryProgramMetadataProvider(
            [self.program_1, self.program_2, self.program_3]
        )
        skill = Skill.objects.all()
        program_skill = ProgramSkill.objects.all()
        self.assertEqual(skill.count(), 0)
        self.assertEqual(program_skill.count(), 0)

        call_command(self.command, '--all', '--commit')

        self.assertEqual(skill.count(), 4)
        self.assertEqual(program_skill.count(), 12)

    @responses.activate
    @mock.patch('taxonomy.management.commands.refresh_program_skills.get_program_metadata_provider')
    @mock.patch('taxonomy.management.commands.refresh_course_skills.utils.EMSISkillsApiClient.get_product_skills')
    @mock.patch('taxonomy.utils.get_translated_skill_attribute_val')
    def test_program_skill_not_saved_upon_exception(self,
                                                    mock_program_description,
                                                    get_product_skills_mock,
                                                    get_program_provider_mock):
        """
        Test that the command does not create any records when the API throws an exception.
        """
        mock_program_description.return_value = 'program overview translation'
        get_product_skills_mock.side_effect = TaxonomyAPIError()
        get_program_provider_mock.return_value = DiscoveryProgramMetadataProvider(
            [self.program_1, self.program_2]
        )
        skill = Skill.objects.all()
        program_skill = ProgramSkill.objects.all()
        self.assertEqual(skill.count(), 0)
        self.assertEqual(program_skill.count(), 0)

        with LogCapture(level=logging.INFO) as log_capture:
            call_command(self.command, '--program', self.program_1.uuid, '--program', self.program_2.uuid, '--commit')
            # Validate a descriptive and readable log message.
            self.assertEqual(len(log_capture.records), 5)
            messages = [record.msg for record in log_capture.records]
            self.assertEqual(
                messages,
                [
                    '[TAXONOMY] Refresh Program Skills. Options: [%s]',
                    '[TAXONOMY] Refresh program skills process started.',
                    '[TAXONOMY] API Error for key: {}'.format(self.program_1.uuid),
                    f'[TAXONOMY] API Error for key: {self.program_2.uuid}',
                    '[TAXONOMY] Refresh %s skills process completed. \n'
                    'Failures: %s \n'
                    'Total %s Updated Successfully: %s \n'
                    'Total %s Skipped: %s \n'
                    'Total Failures: %s \n'
                ]
            )

        self.assertEqual(skill.count(), 0)
        self.assertEqual(program_skill.count(), 0)
