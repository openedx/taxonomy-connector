# -*- coding: utf-8 -*-
"""
Tests for the django management command `refresh_job_skills`.
"""

import logging

import mock
import responses
from ddt import data, ddt
from pytest import mark
from testfixtures import LogCapture

from django.core.management import CommandError, call_command
from django.utils.translation import gettext as _

from taxonomy.enums import RankingFacet
from taxonomy.exceptions import TaxonomyAPIError
from taxonomy.models import Industry, IndustryJobSkill, Job, JobSkills, Skill
from test_utils.factories import SkillFactory
from test_utils.sample_responses.jobs import JOBS, MISSING_SIGNIFICANCE_KEY_JOBS
from test_utils.testcase import TaxonomyTestCase


@ddt
@mark.django_db
class RefreshJobSkillsCommandTests(TaxonomyTestCase):
    """
    Test command `refresh_job_skills`.
    """
    command = 'refresh_job_skills'

    def setUp(self):
        self.jobs = JOBS
        # creating skills
        for job_bucket in self.jobs['data']['ranking']['buckets']:
            for skill_bucket in job_bucket['ranking']['buckets']:
                SkillFactory(external_id=skill_bucket['name'])

        self.mock_access_token()
        super(RefreshJobSkillsCommandTests, self).setUp()

    @responses.activate
    @mock.patch('taxonomy.management.commands.refresh_job_skills.EMSIJobsApiClient.get_jobs')
    @data(False, True)
    def test_job_skills_saved(self, missing_skill, get_job_skills_mock):
        """
        Test that the command creates a Job and many JobSkills records.
        """
        get_job_skills_mock.return_value = self.jobs
        expected_job_count = 2
        expected_job_skill_count = 4
        industry_count = Industry.objects.count()

        if missing_skill:
            # remove one skill
            first_skill = Skill.objects.first()
            Skill.objects.filter(external_id=first_skill.external_id).delete()
            expected_job_skill_count -= 1

        self.assertEqual(Job.objects.count(), 0)
        self.assertEqual(JobSkills.objects.count(), 0)
        self.assertEqual(IndustryJobSkill.objects.count(), 0)

        call_command(self.command)

        self.assertEqual(Job.objects.all().count(), expected_job_count)
        self.assertEqual(JobSkills.objects.all().count(), expected_job_skill_count)
        self.assertEqual(IndustryJobSkill.objects.all().count(), industry_count * expected_job_skill_count)

    @responses.activate
    @mock.patch('taxonomy.management.commands.refresh_job_skills.EMSIJobsApiClient.get_jobs')
    def test_job_skills_not_saved_upon_exception(self, get_job_skills_mock):
        """
        Test that the command does not create any records when the API throws an exception.
        """
        get_job_skills_mock.side_effect = TaxonomyAPIError('Custom error')
        SkillFactory()
        jobs = Job.objects.all()
        job_skills = JobSkills.objects.all()
        self.assertEqual(jobs.count(), 0)
        self.assertEqual(job_skills.count(), 0)

        err_string = _('Taxonomy API Error for refreshing the jobs for Ranking Facet {} and Nested Ranking Facet {}, '
                       'Error: Custom error').format(RankingFacet.TITLE, RankingFacet.SKILLS)
        with LogCapture(level=logging.INFO) as log_capture:
            with self.assertRaisesRegex(CommandError, err_string):
                call_command(self.command)
            # Validate a descriptive and readable log message.
            self.assertEqual(len(log_capture.records), 1)
            message = log_capture.records[0].msg
            self.assertEqual(message, err_string)

        self.assertEqual(jobs.count(), 0)
        self.assertEqual(job_skills.count(), 0)

    @responses.activate
    @mock.patch('taxonomy.management.commands.refresh_job_skills.EMSIJobsApiClient.get_jobs')
    def test_job_skill_not_saved_on_key_error(self, get_jobs_mock):
        """
        Test that the command does not create any records when a key error occurs.
        """
        get_jobs_mock.return_value = MISSING_SIGNIFICANCE_KEY_JOBS
        skills = Skill.objects.all()
        job_skills = JobSkills.objects.all()
        self.assertEqual(skills.count(), 4)
        self.assertEqual(job_skills.count(), 0)

        expected_error_mesg = "Missing keys in update job skills data. Error: 'significance'"
        with LogCapture(level=logging.INFO) as log_capture:
            with self.assertRaisesRegex(CommandError, expected_error_mesg):
                call_command(self.command)
            # Validate a descriptive and readable log message.
            self.assertEqual(len(log_capture.records), 1)
            message = log_capture.records[0].msg
            self.assertEqual(message, expected_error_mesg)

        self.assertEqual(skills.count(), 4)
        self.assertEqual(job_skills.count(), 0)
