# -*- coding: utf-8 -*-
"""
Tests for the django management command `finalize_xblockskill_tag`.
"""
import logging
import responses

from django.core.management import call_command
from testfixtures import LogCapture
from pytest import mark
from test_utils import factories
from test_utils.testcase import TaxonomyTestCase
from test_utils.constants import USAGE_KEY
from taxonomy.models import XBlockSkillData


@mark.django_db
class FinalizeSkillTagsCommandTests(TaxonomyTestCase):
    """
    Test command `finalize_xblockskill_tags`.
    """
    command = 'finalize_xblockskill_tags'

    def setUp(self):
        super().setUp()
        self.mock_access_token()

    @responses.activate
    def test_finalize_xblockskill_tags_without_unverified_skills(self):
        """
        Test that command only shows starting and completed logs
        if no unverified skills exists
        """
        unverified_skills = XBlockSkillData.objects.filter(verified=False)
        self.assertEqual(len(unverified_skills), 0)
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

    @responses.activate
    def test_finalize_xblockskill_tags_below_minimum_votes(self):
        """
        Test that command only shows starting and completed logs
        if verified count is below MIN_VOTES_FOR_SKILLS.
        The MIN_VOTES_FOR_SKILLS value is set to 2 in test_settings
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

    @responses.activate
    def test_finalize_xblockskill_tags_below_ratio_threshold(self):
        """
        Test that command only shows starting and completed logs
        if the ratio of verified_count to ignored_count is below
        the RATIO_THRESHOLD_FOR_SKILLS.
        The RATIO_THRESHOLD_FOR_SKILLS value is set to 0.5 in test_settings
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

    @responses.activate
    def test_finalize_xblockskill_tags(self):
        """
        Test that command shows starting, verified and completed
        logs
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
            call_command(self.command)
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
        updated_xblockskill = XBlockSkillData.objects.all()[0]  # there's only one
        self.assertTrue(updated_xblockskill.verified)
