"""
Tests for taxonomy signals.
"""
import unittest

import mock
from pytest import mark

from taxonomy.models import CourseSkills, Skill, ProgramSkill, XBlockSkills
from taxonomy.signals.signals import UPDATE_COURSE_SKILLS, UPDATE_PROGRAM_SKILLS, UPDATE_XBLOCK_SKILLS
from test_utils.mocks import MockCourse, MockProgram, MockXBlock
from test_utils.providers import (
    DiscoveryCourseMetadataProvider,
    DiscoveryProgramMetadataProvider,
    DiscoveryXBlockMetadataProvider,
)
from test_utils.sample_responses.skills import SKILLS_EMSI_CLIENT_RESPONSE


@mark.django_db
class TaxonomySignalHandlerTests(unittest.TestCase):
    """
    Test class for taxonomy signals.
    """

    def setUp(self):
        self.skills_emsi_client_response = SKILLS_EMSI_CLIENT_RESPONSE
        self.course = MockCourse()
        self.program = MockProgram()
        self.xblock = MockXBlock()
        super().setUp()

    @mock.patch('taxonomy.tasks.get_course_metadata_provider')
    @mock.patch('taxonomy.tasks.utils.EMSISkillsApiClient.get_product_skills')
    def test_update_course_skills_signal_handler(self, get_product_skills_mock, get_course_provider_mock):
        """
        Verify that `UPDATE_COURSE_SKILLS` signal work as expected.
        """
        get_product_skills_mock.return_value = self.skills_emsi_client_response
        get_course_provider_mock.return_value = DiscoveryCourseMetadataProvider([self.course])

        # verify that no `Skill` and `CourseSkills` records exist before executing the task
        skill = Skill.objects.all()
        course_skill = CourseSkills.objects.all()
        self.assertEqual(skill.count(), 0)
        self.assertEqual(course_skill.count(), 0)

        UPDATE_COURSE_SKILLS.send(sender=None, course_uuid=self.course.uuid)

        self.assertEqual(skill.count(), 4)
        self.assertEqual(course_skill.count(), 4)

    @mock.patch('taxonomy.tasks.get_program_metadata_provider')
    @mock.patch('taxonomy.tasks.utils.EMSISkillsApiClient.get_product_skills')
    def test_update_program_skills_signal_handler(self, get_product_skills_mock, get_program_provider_mock):
        """
        Verify that `UPDATE_PROGRAM_SKILLS` signal work as expected.
        """
        get_product_skills_mock.return_value = self.skills_emsi_client_response
        get_program_provider_mock.return_value = DiscoveryProgramMetadataProvider([self.program])

        # verify that no `Skill` and `ProgramSkill` records exist before executing the task
        skill = Skill.objects.all()
        program_skill = ProgramSkill.objects.all()
        self.assertEqual(skill.count(), 0)
        self.assertEqual(program_skill.count(), 0)

        UPDATE_PROGRAM_SKILLS.send(sender=None, program_uuid=self.program.uuid)

        self.assertEqual(skill.count(), 4)
        self.assertEqual(program_skill.count(), 4)

    @mock.patch('taxonomy.tasks.get_xblock_metadata_provider')
    @mock.patch('taxonomy.tasks.utils.EMSISkillsApiClient.get_product_skills')
    def test_update_xblock_skills_signal_handler(self, get_product_skills_mock, get_block_provider_mock):
        """
        Verify that `UPDATE_XBLOCK_SKILLS` signal work as expected.
        """
        get_product_skills_mock.return_value = self.skills_emsi_client_response
        get_block_provider_mock.return_value = DiscoveryXBlockMetadataProvider([self.xblock])

        # verify that no `Skill` and `XBlockSkills` records exist before executing the task
        skill = Skill.objects.all()
        xblock_skill = XBlockSkills.objects.all()
        self.assertEqual(skill.count(), 0)
        self.assertEqual(xblock_skill.count(), 0)

        UPDATE_XBLOCK_SKILLS.send(sender=None, xblock_uuid=self.xblock.key)

        self.assertEqual(skill.count(), 4)
        self.assertEqual(xblock_skill.count(), 1)
        self.assertEqual(xblock_skill.first().skills.count(), 4)
