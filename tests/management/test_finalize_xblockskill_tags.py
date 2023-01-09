# -*- coding: utf-8 -*-
"""
Tests for the django management command `finalize_xblockskill_tag`.
"""
import logging

from pytest import mark
from testfixtures import LogCapture

from django.core.management import call_command
from django.test import override_settings

from taxonomy.exceptions import InvalidCommandOptionsError
from taxonomy.models import XBlockSkillData
from test_utils import factories
from test_utils.constants import USAGE_KEY
from test_utils.testcase import TaxonomyTestCase


@mark.django_db
class FinalizeSkillTagsCommandTests(TaxonomyTestCase):
    """
    Test command `finalize_xblockskill_tags`.
    """
    command = 'finalize_xblockskill_tags'

    def setUp(self):
        super().setUp()
        self.mock_access_token()

    def test_finalize_xblockskill_tags_without_unverified_skills(self):
        """
        Test that command only shows starting and completed logs
        if no unverified skills exists
        """
        unverified_skills = XBlockSkillData.objects.filter(verified=False)
        self.assertEqual(len(unverified_skills), 0)
        with LogCapture(level=logging.INFO) as log_capture:
            call_command(self.command, min_verified_votes=2, ratio_verified_threshold=0.5)
            self.assertEqual(len(log_capture.records), 2)
            messages = [record.msg for record in log_capture.records]
            self.assertEqual(
                messages,
                [
                    'Starting xblockskill tags verification task',
                    'Xblockskill tags verification task is completed'
                ]
            )

    def test_finalize_xblockskill_tags_below_minimum_votes(self):
        """
        Test that command only shows starting and completed logs
        if verified count is below minimum votes.
        The minimum votes can either be configured in settings file
        using MIN_VOTES_FOR_SKILLS or passed in as an optional parameter.
        """
        xblock = factories.XBlockSkillsFactory(usage_key=USAGE_KEY)
        xblock_skill = factories.XBlockSkillDataFactory(xblock=xblock)

        # ensure xblockskilldata object is created
        unverified_skills = XBlockSkillData.objects.filter(verified=False)
        self.assertEqual(len(unverified_skills), 1)

        # Set the verified count to a value below the MIN_VOTES_FOR_SKILLS
        xblock_skill.verified_count = 1
        xblock_skill.ignored_count = 0
        xblock_skill.save()
        with LogCapture(level=logging.INFO) as log_capture:
            call_command(self.command, min_verified_votes=2, ratio_verified_threshold=0.5)
            self.assertEqual(len(log_capture.records), 2)
            messages = [record.msg for record in log_capture.records]
            self.assertEqual(
                messages,
                [
                    'Starting xblockskill tags verification task',
                    'Xblockskill tags verification task is completed'
                ]
            )

    def test_finalize_xblockskill_tags_below_ratio_threshold(self):
        """
        Test that command only shows starting and completed logs
        if the ratio of verified_count to ignored_count is below
        the ratio threshold.
        The ratio threshold can either be configured in the settings
        file using RATIO_THRESHOLD_FOR_SKILLS or passed in as an
        optional parameter.
        """
        xblock = factories.XBlockSkillsFactory(usage_key=USAGE_KEY)
        xblock_skill = factories.XBlockSkillDataFactory(xblock=xblock)

        # ensure xblockskilldata object is created
        unverified_skills = XBlockSkillData.objects.filter(verified=False)
        self.assertEqual(len(unverified_skills), 1)

        # Set the verified count and ignored count so that their ratio
        # is below the RATIO_THRESHOLD_FOR_SKILLS
        xblock_skill.verified_count = 1
        xblock_skill.ignored_count = 3
        xblock_skill.save()
        with LogCapture(level=logging.INFO) as log_capture:
            call_command(self.command, min_verified_votes=2, ratio_verified_threshold=0.5)
            self.assertEqual(len(log_capture.records), 2)
            messages = [record.msg for record in log_capture.records]
            self.assertEqual(
                messages,
                [
                    'Starting xblockskill tags verification task',
                    'Xblockskill tags verification task is completed'
                ]
            )

    def test_finalize_xblockskill_tags_for_verification(self):
        """
        Test that finalize_xblockskill_tags verifies skills with correct votes.
        """
        xblock = factories.XBlockSkillsFactory(usage_key=USAGE_KEY)
        xblock_skill = factories.XBlockSkillDataFactory(xblock=xblock)

        # ensure xblockskilldata object is created
        unverified_skills = XBlockSkillData.objects.filter(verified=False)
        self.assertEqual(len(unverified_skills), 1)

        # Set the verified count and ignored count so that the ratio is above
        # the RATIO_THRESHOLD_FOR_SKILLS
        xblock_skill.verified_count = 3
        xblock_skill.ignored_count = 1
        xblock_skill.save()
        with LogCapture(level=logging.INFO) as log_capture:
            call_command(self.command, min_verified_votes=2, ratio_verified_threshold=0.5)
            self.assertEqual(len(log_capture.records), 3)
            messages = [record.msg for record in log_capture.records]
            self.assertEqual(
                messages,
                [
                    'Starting xblockskill tags verification task',
                    '[%s] skill tag for the xblock [%s] has been verified',
                    'Xblockskill tags verification task is completed'
                ]
            )
        updated_xblockskill = XBlockSkillData.objects.first()  # there's only one
        self.assertTrue(updated_xblockskill.verified)

    @override_settings(SKILLS_VERIFICATION_THRESHOLD=None)
    def test_finalize_xblockskill_tags_without_settings(self):
        """
        Test that command raises InvalidCommandOptionsError if any setting and
        argument is missing.
        """
        with self.assertRaises(InvalidCommandOptionsError):
            call_command(self.command)

    def test_finalize_xblockskill_tags_with_no_votes(self):
        """
        Test that command does nothing if no votes are present for given block
        """
        xblock = factories.XBlockSkillsFactory(usage_key=USAGE_KEY)
        factories.XBlockSkillDataFactory(xblock=xblock)

        # ensure xblockskilldata object is created
        unverified_skills = XBlockSkillData.objects.filter(verified=False)
        self.assertEqual(unverified_skills.count(), 1)

        with LogCapture(level=logging.INFO) as log_capture:
            call_command(self.command)
            self.assertEqual(len(log_capture.records), 2)
            messages = [record.msg for record in log_capture.records]
            self.assertEqual(
                messages,
                [
                    'Starting xblockskill tags verification task',
                    'Xblockskill tags verification task is completed'
                ]
            )
        self.assertEqual(unverified_skills.count(), 1)

    def test_finalize_xblockskill_tags_for_blacklisting(self):
        """
        Test that finalize_xblockskill_tags blacklists highly ignored skills.
        """
        xblock = factories.XBlockSkillsFactory(usage_key=USAGE_KEY)
        xblock_skill = factories.XBlockSkillDataFactory(xblock=xblock)

        # ensure xblockskilldata object is created
        unverified_skills = XBlockSkillData.objects.filter(verified=False, is_blacklisted=False)
        self.assertEqual(len(unverified_skills), 1)

        # Set the verified count and ignored count so that the ratio is above
        # the RATIO_THRESHOLD_FOR_SKILLS
        xblock_skill.verified_count = 2
        xblock_skill.ignored_count = 20
        xblock_skill.save()
        with LogCapture(level=logging.INFO) as log_capture:
            call_command(self.command)
            self.assertEqual(len(log_capture.records), 3)
            messages = [record.msg for record in log_capture.records]
            self.assertEqual(
                messages,
                [
                    'Starting xblockskill tags verification task',
                    '[%s] skill tag for the xblock [%s] has been blacklisted',
                    'Xblockskill tags verification task is completed'
                ]
            )
        updated_xblockskill = XBlockSkillData.objects.first()  # there's only one
        self.assertFalse(updated_xblockskill.verified)
        self.assertTrue(updated_xblockskill.is_blacklisted)

    def test_argument_has_priority(self):
        """
        Test that command argument has priority over settings.
        """
        xblock = factories.XBlockSkillsFactory(usage_key=USAGE_KEY)
        xblock_skill = factories.XBlockSkillDataFactory(xblock=xblock)

        # ensure xblockskilldata object is created
        unverified_skills = XBlockSkillData.objects.filter(verified=False)
        self.assertEqual(len(unverified_skills), 1)

        # Set the verified count and ignored count so that the ratio is above
        # the settings.SKILLS_VERIFICATION_THRESHOLD and settings.SKILLS_VERIFICATION_RATIO_THRESHOLD
        xblock_skill.verified_count = 3
        xblock_skill.ignored_count = 1
        xblock_skill.save()
        with LogCapture(level=logging.INFO) as log_capture:
            # setting thresholds higher than settings
            call_command(self.command, min_verified_votes=8, ratio_verified_threshold=0.9)
            self.assertEqual(len(log_capture.records), 2)
            messages = [record.msg for record in log_capture.records]
            self.assertEqual(
                messages,
                [
                    'Starting xblockskill tags verification task',
                    'Xblockskill tags verification task is completed'
                ]
            )
        updated_xblockskill = XBlockSkillData.objects.first()  # there's only one
        self.assertFalse(updated_xblockskill.verified)
