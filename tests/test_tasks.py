"""
Tests for celery tasks.
"""
import logging
import unittest

import mock
from pytest import mark
from testfixtures import LogCapture

from taxonomy.models import CourseSkills, Skill, ProgramSkill, XBlockSkills
from taxonomy.tasks import update_course_skills, update_program_skills, update_xblock_skills
from test_utils.mocks import MockCourse, MockProgram, MockXBlock
from test_utils.providers import (
    DiscoveryCourseMetadataProvider,
    DiscoveryProgramMetadataProvider,
    DiscoveryXBlockMetadataProvider,
)
from test_utils.sample_responses.skills import SKILLS_EMSI_CLIENT_RESPONSE


@mark.django_db
class TaxonomyTasksTests(unittest.TestCase):
    """
    Tests for taxonomy celery tasks.
    """

    def setUp(self):
        self.skills_emsi_client_response = SKILLS_EMSI_CLIENT_RESPONSE
        self.course = MockCourse()
        self.program = MockProgram()
        self.xblock = MockXBlock()
        super().setUp()

    def check_empty_skill_models(self, product_skill_model):
        """
        verify that no Skill and CourseSkills/ProgramSkill records exist before executing the task
        """
        skill = Skill.objects.all()
        product_skill = product_skill_model.objects.all()
        self.assertEqual(skill.count(), 0)
        self.assertEqual(product_skill.count(), 0)

        return skill, product_skill

    @mock.patch('taxonomy.tasks.get_course_metadata_provider')
    @mock.patch('taxonomy.tasks.utils.EMSISkillsApiClient.get_product_skills')
    def test_update_course_skills_task(self, get_course_skills_mock, get_course_provider_mock):
        """
        Verify that `update_course_skills` task work as expected.
        """
        get_course_skills_mock.return_value = self.skills_emsi_client_response
        get_course_provider_mock.return_value = DiscoveryCourseMetadataProvider([self.course])

        skill, course_skill = self.check_empty_skill_models(CourseSkills)

        update_course_skills.delay([self.course.uuid])

        self.assertEqual(skill.count(), 4)
        self.assertEqual(course_skill.count(), 4)

    @mock.patch('taxonomy.tasks.get_course_metadata_provider')
    @mock.patch('taxonomy.tasks.utils.EMSISkillsApiClient.get_product_skills')
    def test_update_course_skills_task_with_no_course_found(self, get_course_skills_mock, get_course_provider_mock):
        """
        Verify that `update_skills` task work as expected.
        """
        get_course_skills_mock.return_value = self.skills_emsi_client_response
        get_course_provider_mock.return_value = DiscoveryCourseMetadataProvider([])

        skill, course_skill = self.check_empty_skill_models(CourseSkills)

        with LogCapture(level=logging.INFO) as log_capture:
            update_course_skills.delay([self.course.uuid])
            messages = [record.msg for record in log_capture.records]
            self.assertEqual(
                messages,
                [
                    '[TAXONOMY] refresh_course_skills task triggered',
                    '[TAXONOMY] No course found with uuids [%d] to update skills.',
                    'Task %(name)s[%(id)s] succeeded in %(runtime)ss: %(return_value)s'
                ]
            )

        self.assertEqual(skill.count(), 0)
        self.assertEqual(course_skill.count(), 0)

    @mock.patch('taxonomy.tasks.get_program_metadata_provider')
    @mock.patch('taxonomy.tasks.utils.EMSISkillsApiClient.get_product_skills')
    def test_update_program_skills_task(self, get_program_skills_mock, mock_get_provider):
        """
        Verify that `update_program_skills` task work as expected.
        """
        get_program_skills_mock.return_value = self.skills_emsi_client_response
        mock_get_provider.return_value = DiscoveryProgramMetadataProvider([self.program])

        skill, program_skill = self.check_empty_skill_models(ProgramSkill)

        update_program_skills.delay([self.program.uuid])

        self.assertEqual(skill.count(), 4)
        self.assertEqual(program_skill.count(), 4)

    @mock.patch('taxonomy.tasks.get_program_metadata_provider')
    @mock.patch('taxonomy.tasks.utils.EMSISkillsApiClient.get_product_skills')
    def test_update_program_skills_task_with_no_program_found(
            self, get_program_skills_mock, mock_get_provider):
        """
        Verify that `update_program_skills` task work as expected.
        """
        get_program_skills_mock.return_value = self.skills_emsi_client_response
        mock_get_provider.return_value = DiscoveryProgramMetadataProvider([])

        skill, program_skill = self.check_empty_skill_models(ProgramSkill)

        with LogCapture(level=logging.INFO) as log_capture:
            update_program_skills.delay([self.program.uuid])
            messages = [record.msg for record in log_capture.records]
            self.assertEqual(
                messages,
                [
                    '[TAXONOMY] refresh_program_skills task triggered',
                    '[TAXONOMY] No program found with uuids [%d] to update skills.',
                    'Task %(name)s[%(id)s] succeeded in %(runtime)ss: %(return_value)s'
                ]
            )

        self.assertEqual(skill.count(), 0)
        self.assertEqual(program_skill.count(), 0)

    @mock.patch('taxonomy.tasks.get_xblock_metadata_provider')
    @mock.patch('taxonomy.tasks.utils.EMSISkillsApiClient.get_product_skills')
    def test_update_xblock_skills_task(self, get_xblock_skills_mock, get_xblock_provider_mock):
        """
        Verify that `update_xblock_skills` task work as expected.
        """
        get_xblock_skills_mock.return_value = self.skills_emsi_client_response
        get_xblock_provider_mock.return_value = DiscoveryXBlockMetadataProvider([self.xblock])

        skill, xblock_skill = self.check_empty_skill_models(XBlockSkills)

        update_xblock_skills.delay([self.xblock.key])

        self.assertEqual(skill.count(), 4)
        self.assertEqual(xblock_skill.count(), 1)
        self.assertEqual(xblock_skill.first().skills.count(), 4)

    @mock.patch('taxonomy.tasks.get_xblock_metadata_provider')
    @mock.patch('taxonomy.tasks.utils.EMSISkillsApiClient.get_product_skills')
    def test_update_xblock_skills_task_with_no_xblock_found(self, get_xblock_skills_mock, get_xblock_provider_mock):
        """
        Verify that `update_skills` task work as expected.
        """
        get_xblock_skills_mock.return_value = self.skills_emsi_client_response
        get_xblock_provider_mock.return_value = DiscoveryXBlockMetadataProvider([])

        skill, xblock_skill = self.check_empty_skill_models(XBlockSkills)

        with LogCapture(level=logging.INFO) as log_capture:
            update_xblock_skills.delay([self.xblock.key])
            messages = [record.msg for record in log_capture.records]
            self.assertEqual(
                messages,
                [
                    '[TAXONOMY] refresh_xblock_skills task triggered',
                    '[TAXONOMY] No xblock found with uuids [%d] to update skills.',
                    'Task %(name)s[%(id)s] succeeded in %(runtime)ss: %(return_value)s'
                ]
            )

        self.assertEqual(skill.count(), 0)
        self.assertEqual(xblock_skill.count(), 0)
