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
from taxonomy.exceptions import InvalidCommandOptionsError


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
            call_command(self.command, min_votes=2, ratio_threshold=0.5)
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
            call_command(self.command, min_votes=2, ratio_threshold=0.5)
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
            call_command(self.command, min_votes=2, ratio_threshold=0.5)
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
            call_command(self.command, min_votes=2, ratio_threshold=0.5)
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

    @responses.activate
    def test_finalize_xblockskill_tags_without_min_votes(self):
        """
        Test that command raises InvalidCommandOption error if
        minimum votes is not set in the settings file or sent in
        as a parameter
        """
        xblock = factories.XBlockSkillsFactory(usage_key=USAGE_KEY)
        xblock_skill = factories.XBlockSkillDataFactory(xblock=xblock)

        # ensure xblockskilldata object is created
        unverified_skills = XBlockSkillData.objects.filter(verified=False)
        self.assertEqual(len(unverified_skills), 1)

        xblock_skill.verified_count = 1
        xblock_skill.ignored_count = 0
        xblock_skill.save()

        error_str = 'Either configure MIN_VOTES_FOR_SKILLS in settings or pass with arg --min-votes'
        with LogCapture(level=logging.INFO) as log_capture:
            with self.assertRaisesRegex(InvalidCommandOptionsError, error_str):
                call_command(self.command, ratio_threshold=0.5)
            self.assertEqual(len(log_capture.records), 1)
            message = log_capture.records[0].msg
            # only the staring message will be shown
            self.assertEqual(
                message,
                'Starting xblockskill tags verification task',
            )

    @responses.activate
    def test_finalize_xblockskill_tags_without_ratio_threshold(self):
        """
        Test that command raises InvalidCommandOption error if the
        ratio threshold is not set in the settings file or sent in
        as a parameter
        """
        xblock = factories.XBlockSkillsFactory(usage_key=USAGE_KEY)
        xblock_skill = factories.XBlockSkillDataFactory(xblock=xblock)

        # ensure xblockskilldata object is created
        unverified_skills = XBlockSkillData.objects.filter(verified=False)
        self.assertEqual(len(unverified_skills), 1)

        xblock_skill.verified_count = 1
        xblock_skill.ignored_count = 0
        xblock_skill.save()

        error_str = 'Either configure RATIO_THRESHOLD_FOR_SKILLS in settings or pass with arg --ratio-threshold'
        with LogCapture(level=logging.INFO) as log_capture:
            with self.assertRaisesRegex(InvalidCommandOptionsError, error_str):
                call_command(self.command, min_votes=2)
            self.assertEqual(len(log_capture.records), 1)
            message = log_capture.records[0].msg
            # only the staring message will be shown
            self.assertEqual(
                message,
                'Starting xblockskill tags verification task',
            )

    @responses.activate
    def test_finalize_xblockskill_tags_without_any_counts(self):
        """
        Test that command only shows starting and completed logs
        if the skills have neither verified not ignored counts
        """
        xblock = factories.XBlockSkillsFactory(usage_key=USAGE_KEY)
        xblock_skill = factories.XBlockSkillDataFactory(xblock=xblock)

        # ensure xblockskilldata object is created
        unverified_skills = XBlockSkillData.objects.filter(verified=False)
        self.assertEqual(len(unverified_skills), 1)

        xblock_skill.verified_count = 0
        xblock_skill.ignored_count = 0
        xblock_skill.save()

        with LogCapture(level=logging.INFO) as log_capture:
            call_command(self.command, min_votes=2, ratio_threshold=0.5)
            self.assertEqual(len(log_capture.records), 2)
            messages = [record.msg for record in log_capture.records]
            self.assertEqual(
                messages,
                [
                    'Starting xblockskill tags verification task',
                    'Xblockskill tags verification task is completed'
                ]
            )
