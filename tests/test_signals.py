"""
Tests for taxonomy signals.
"""
import logging
import unittest

import mock
from pytest import mark
from testfixtures import LogCapture
from openedx_events.content_authoring.data import DuplicatedXBlockData, XBlockData
from openedx_events.content_authoring.signals import XBLOCK_DELETED, XBLOCK_DUPLICATED, XBLOCK_PUBLISHED
from openedx_events.learning.data import XBlockSkillVerificationData
from openedx_events.learning.signals import XBLOCK_SKILL_VERIFIED

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
            (XBLOCK_SKILL_VERIFIED, "XBLOCK_SKILL_VERIFIED"),
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

    @mock.patch('taxonomy.tasks.get_xblock_metadata_provider')
    @mock.patch('taxonomy.tasks.utils.EMSISkillsApiClient.get_product_skills')
    def test_xblock_skills_verification_signals(self, get_product_skills_mock, get_block_provider_mock):
        """
        Verify that `XBLOCK_SKILL_VERIFIED` signal is handled as expected.
        """
        # setup, create xblock and related skills
        get_product_skills_mock.return_value = self.skills_emsi_client_response
        get_block_provider_mock.return_value = DiscoveryXBlockMetadataProvider([self.xblock])
        XBLOCK_PUBLISHED.send_event(
            xblock_info=XBlockData(
                usage_key=self.xblock.key,
                block_type=self.xblock.content_type,
            ),
        )

        self.assertEqual(XBlockSkillData.objects.all().count(), 4)
        self.assertEqual(sum(XBlockSkillData.objects.all().values_list("verified_count", flat=True)), 0)
        self.assertEqual(sum(XBlockSkillData.objects.all().values_list("ignored_count", flat=True)), 0)
        skill_ids = list(XBlockSkillData.objects.all().values_list("skill_id", flat=True))

        # action
        XBLOCK_SKILL_VERIFIED.send_event(
            xblock_info=XBlockSkillVerificationData(
                usage_key=self.xblock.key,
                verified_skills=skill_ids[:2],
                ignored_skills=skill_ids[2:],
            )
        )
        # verify
        self.assertEqual(list(XBlockSkillData.objects.all().values_list("verified_count", flat=True)), [1, 1, 0, 0])
        self.assertEqual(list(XBlockSkillData.objects.all().values_list("ignored_count", flat=True)), [0, 0, 1, 1])

        # double check
        XBLOCK_SKILL_VERIFIED.send_event(
            xblock_info=XBlockSkillVerificationData(
                usage_key=self.xblock.key,
                verified_skills=skill_ids[:2],
                ignored_skills=skill_ids[2:],
            )
        )
        self.assertEqual(list(XBlockSkillData.objects.all().values_list("verified_count", flat=True)), [2, 2, 0, 0])
        self.assertEqual(list(XBlockSkillData.objects.all().values_list("ignored_count", flat=True)), [0, 0, 2, 2])

    def test_missing_xblock_skills_verification_signals(self):
        """
        Verify that `XBLOCK_SKILL_VERIFIED` signal does nothing if xblock does not exists.
        """

        with LogCapture(level=logging.INFO) as log_capture:
            XBLOCK_SKILL_VERIFIED.send_event(
                xblock_info=XBlockSkillVerificationData(
                    usage_key=self.xblock.key,
                    verified_skills=[1],
                    ignored_skills=[],
                )
            )
            messages = [record.msg for record in log_capture.records]
            self.assertEqual(len(log_capture.records), 6)
            self.assertEqual(
                [
                    f'[TAXONOMY] XBLOCK_SKILL_VERIFIED signal received',
                    '[TAXONOMY] update_xblock_skills_verification_counts task triggered',
                    f'[TAXONOMY] XBlock with usage_key: {self.xblock.key} not found!',
                    '[TAXONOMY] update_xblock_skills_verification_counts task completed',
                ],
                messages[:-2]
            )

    def test_empty_skills_for_xblock_verification_signals(self):
        """
        Verify that `XBLOCK_SKILL_VERIFIED` signal does nothing if both
        verified and ignored skill list are empty.
        """

        with LogCapture(level=logging.INFO) as log_capture:
            XBLOCK_SKILL_VERIFIED.send_event(
                xblock_info=XBlockSkillVerificationData(
                    usage_key=self.xblock.key,
                    verified_skills=[],
                    ignored_skills=[],
                )
            )
            messages = [record.msg for record in log_capture.records]
            self.assertEqual(len(log_capture.records), 3)
            self.assertEqual(
                [
                    f'[TAXONOMY] XBLOCK_SKILL_VERIFIED signal received',
                    '[TAXONOMY] Missing verified and ignored skills list.',
                ],
                messages[:-1]
            )
