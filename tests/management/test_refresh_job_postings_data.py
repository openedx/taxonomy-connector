# -*- coding: utf-8 -*-
"""
Tests for the django management command `refresh_job_postings_data`.
"""

import logging

import mock
from pytest import mark
from testfixtures import LogCapture

from django.core.management import CommandError, call_command
from django.test import TestCase
from django.utils.translation import gettext as _

from taxonomy.exceptions import TaxonomyAPIError
from taxonomy.models import Job, JobPostings
from test_utils.sample_responses.job_postings import JOB_POSTINGS, MISSING_MEDIAN_SALARY_JOB_POSTING


@mark.django_db
class RefreshJobPostingsCommandTests(TestCase):
    """
    Test command `refresh_job_postings_data`.
    """

    command = 'refresh_job_postings_data'

    def setUp(self):
        """
        Testcase Setup.
        """
        self.job_postings_data = JOB_POSTINGS
        self.missing_median_salary = MISSING_MEDIAN_SALARY_JOB_POSTING
        super(RefreshJobPostingsCommandTests, self).setUp()

    @mock.patch('taxonomy.management.commands.refresh_job_skills.EMSIJobsApiClient.get_job_postings')
    def test_job_postings_saved(self, get_job_postings_mock):
        """
        Test that the command creates Job and JobPostings.
        """
        get_job_postings_mock.return_value = self.job_postings_data
        jobs = Job.objects.all()
        job_postings = JobPostings.objects.all()
        self.assertEqual(jobs.count(), 0)
        self.assertEqual(job_postings.count(), 0)

        call_command(self.command, 'TITLE_NAME')

        self.assertEqual(jobs.count(), 3)
        self.assertEqual(job_postings.count(), 3)

    def test_missing_argument(self):
        """
        Test that an error message is shown if the command argument is missing.
        """
        err_string = _('Error: the following arguments are required: ranking_facet')
        with self.assertRaisesRegex(CommandError, err_string):
            call_command(self.command)

    @mock.patch('taxonomy.management.commands.refresh_job_skills.EMSIJobsApiClient.get_job_postings')
    def test_job_postings_not_saved_upon_exception(self, get_job_postings_mock):
        """
        Test that the command does not create any records when the API throws an exception.
        """
        get_job_postings_mock.side_effect = TaxonomyAPIError()
        jobs = Job.objects.all()
        job_postings = JobPostings.objects.all()
        self.assertEqual(jobs.count(), 0)
        self.assertEqual(job_postings.count(), 0)

        err_string = _('Taxonomy API Error for refreshing the job postings data for Ranking Facet TITLE_NAME')
        with LogCapture(level=logging.INFO) as log_capture:
            with self.assertRaisesRegex(CommandError, err_string):
                call_command(self.command, 'TITLE_NAME')
            # Validate a descriptive and readable log message.
            self.assertEqual(len(log_capture.records), 1)
            message = log_capture.records[0].msg
            self.assertEqual(
                message,
                'Taxonomy API Error for refreshing the job postings data for Ranking Facet TITLE_NAME'
            )

        self.assertEqual(jobs.count(), 0)
        self.assertEqual(job_postings.count(), 0)

    @mock.patch('taxonomy.management.commands.refresh_job_skills.EMSIJobsApiClient.get_job_postings')
    def test_job_postings_not_saved_on_key_error(self, get_job_postings_mock):
        """
        Test that the command does not create any records when a key error occurs.
        """
        get_job_postings_mock.return_value = self.missing_median_salary
        jobs = Job.objects.all()
        job_postings = JobPostings.objects.all()
        self.assertEqual(jobs.count(), 0)
        self.assertEqual(job_postings.count(), 0)

        err_string = _('Missing keys in job postings data')
        with LogCapture(level=logging.INFO) as log_capture:
            with self.assertRaisesRegex(CommandError, err_string):
                call_command(self.command, 'TITLE_NAME')
            # Validate a descriptive and readable log message.
            self.assertEqual(len(log_capture.records), 1)
            message = log_capture.records[0].msg
            self.assertEqual(message, 'Missing keys in job postings data')

        self.assertEqual(jobs.count(), 0)
        self.assertEqual(job_postings.count(), 0)
