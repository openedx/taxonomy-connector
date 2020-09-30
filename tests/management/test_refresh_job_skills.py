# -*- coding: utf-8 -*-
"""
Tests for the django management command `refresh_job_skills`.
"""

import logging

import mock
from pytest import mark
from testfixtures import LogCapture

from django.core.management import CommandError, call_command
from django.test import TestCase
from django.utils.translation import gettext as _

from taxonomy.exceptions import TaxonomyAPIError
from taxonomy.models import Job, JobSkills
from test_utils.sample_responses.jobs import JOBS


@mark.django_db
class RefreshJobSkillsCommandTests(TestCase):
    """
    Test command `refresh_job_skills`.
    """
    command = 'refresh_job_skills'

    def setUp(self):
        self.jobs = JOBS
        super(RefreshJobSkillsCommandTests, self).setUp()

    @mock.patch('taxonomy.management.commands.refresh_job_skills.EMSIJobsApiClient.get_jobs')
    def test_job_skills_saved(self, get_job_skills_mock):
        """
        Test that the command creates a Job and many JobSkills records.
        """
        get_job_skills_mock.return_value = self.jobs
        jobs = Job.objects.all()
        job_skills = JobSkills.objects.all()
        self.assertEqual(jobs.count(), 0)
        self.assertEqual(job_skills.count(), 0)

        call_command(self.command, 'CERTIFICATIONS', 'CERTIFICATIONS_NAME')

        self.assertEqual(jobs.count(), 2)
        self.assertEqual(job_skills.count(), 4)

    def test_missing_arguments(self):
        """
        Test missing arguments.
        """
        err_string = _('Error: the following arguments are required: ranking_facet, nested_ranking_facet')
        with self.assertRaisesRegex(CommandError, err_string):
            call_command(self.command)

    @mock.patch('taxonomy.management.commands.refresh_job_skills.EMSIJobsApiClient.get_jobs')
    def test_job_skills_not_saved_upon_exception(self, get_job_skills_mock):
        """
        Test that the command does not create any records when the API throws an exception.
        """
        get_job_skills_mock.side_effect = TaxonomyAPIError()
        jobs = Job.objects.all()
        job_skills = JobSkills.objects.all()
        self.assertEqual(jobs.count(), 0)
        self.assertEqual(job_skills.count(), 0)

        err_string = _('Taxonomy API Error for refreshing the jobs for Ranking Facet'
                       ' CERTIFICATIONS and Nested Ranking Facet CERTIFICATIONS_NAME')
        with LogCapture(level=logging.INFO) as log_capture:
            with self.assertRaisesRegex(CommandError, err_string):
                call_command(self.command, 'CERTIFICATIONS', 'CERTIFICATIONS_NAME')
            # Validate a descriptive and readable log message.
            self.assertEqual(len(log_capture.records), 1)
            message = log_capture.records[0].msg
            self.assertEqual(message, 'Taxonomy API Error for refreshing the jobs for'
                                      ' Ranking Facet CERTIFICATIONS and Nested Ranking Facet CERTIFICATIONS_NAME')

        self.assertEqual(jobs.count(), 0)
        self.assertEqual(job_skills.count(), 0)
