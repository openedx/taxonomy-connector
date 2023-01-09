"""
Tests for taxonomy signals.
"""
import logging
import unittest

import mock
from openedx_events.content_authoring.data import DuplicatedXBlockData, XBlockData
from openedx_events.content_authoring.signals import XBLOCK_DELETED, XBLOCK_DUPLICATED, XBLOCK_PUBLISHED
from pytest import mark
from testfixtures import LogCapture

from taxonomy.models import CourseSkills, Skill, ProgramSkill, XBlockSkillData, XBlockSkills
from taxonomy.signals.signals import (
    UPDATE_COURSE_SKILLS,
    UPDATE_PROGRAM_SKILLS,
    UPDATE_XBLOCK_SKILLS,
)
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
    def test_xblock_skill_update_and_deleted_signal_handlers(self, get_product_skills_mock, get_block_provider_mock):
        """
        Verify that `UPDATE_XBLOCK_SKILLS` and `XBLOCK_DELETED` signal work as
        expected.
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

        XBLOCK_DELETED.send_event(
            xblock_info=XBlockData(
                usage_key=self.xblock.key,
                block_type=self.xblock.content_type,
            ),
        )
        self.assertEqual(xblock_skill.count(), 0)
        self.assertEqual(XBlockSkillData.objects.all().count(), 0)
        self.assertEqual(skill.count(), 4)

    @mock.patch('taxonomy.tasks.get_xblock_metadata_provider')
    @mock.patch('taxonomy.tasks.utils.EMSISkillsApiClient.get_product_skills')
    def test_xblock_skill_published_and_duplicated_signals(self, get_product_skills_mock, get_block_provider_mock):
        """
        Verify that `XBLOCK_PUBLISHED` & `XBLOCK_DUPLICATED` signal work as expected.
        """
        get_product_skills_mock.return_value = self.skills_emsi_client_response
        get_block_provider_mock.return_value = DiscoveryXBlockMetadataProvider([self.xblock])

        # verify that no `Skill` and `XBlockSkills` records exist before executing the task
        skill = Skill.objects.all()
        xblock_skill = XBlockSkills.objects.all()
        self.assertEqual(skill.count(), 0)
        self.assertEqual(xblock_skill.count(), 0)

        XBLOCK_PUBLISHED.send_event(
            xblock_info=XBlockData(
                usage_key=self.xblock.key,
                block_type=self.xblock.content_type,
            ),
        )

        self.assertEqual(skill.count(), 4)
        self.assertEqual(xblock_skill.count(), 1)
        self.assertEqual(xblock_skill.first().skills.count(), 4)
        self.assertEqual(XBlockSkillData.objects.all().count(), 4)

        dup_xblock = MockXBlock()
        XBLOCK_DUPLICATED.send_event(
            xblock_info=DuplicatedXBlockData(
                usage_key=dup_xblock.key,
                block_type=self.xblock.content_type,
                source_usage_key=self.xblock.key,
            ),
        )
        self.assertEqual(skill.count(), 4)
        self.assertEqual(xblock_skill.count(), 2)
        new_xblock = xblock_skill.get(usage_key=dup_xblock.key)
        self.assertEqual(XBlockSkillData.objects.filter(xblock=new_xblock).count(), 4)

    def test_empty_event_data_format_skips_processing(self):
        """
        Verify that incorrect data passed via openedx_events skips processing.
        """
        events = [
            (XBLOCK_PUBLISHED, "XBLOCK_PUBLISHED"),
            (XBLOCK_DELETED, "XBLOCK_DELETED"),
            (XBLOCK_DUPLICATED, "XBLOCK_DUPLICATED"),
        ]
        for event, name in events:
            correct_init_data = event.init_data
            # disable validation in publishing side
            event.init_data = {}
            with LogCapture(level=logging.INFO) as log_capture:
                # send empty event
                event.send_event()
                # reset validation in events
                event.init_data = correct_init_data
                # Validate a descriptive and readable log message.
                messages = [record.msg for record in log_capture.records]
                self.assertEqual(len(log_capture.records), 3)
                self.assertEqual(
                    [
                        f'[TAXONOMY] {name} signal received',
                        f'[TAXONOMY] Received null or incorrect data from {name}.',
                    ],
                    messages[:-1]
                )
