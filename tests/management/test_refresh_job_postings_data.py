# -*- coding: utf-8 -*-
"""
Tests for the django management command `refresh_job_postings_data`.
"""

import logging

import mock
import responses
from ddt import data, ddt
from pytest import mark
from testfixtures import LogCapture

from django.core.management import CommandError, call_command
from django.utils.translation import gettext as _

from taxonomy.exceptions import TaxonomyAPIError
from taxonomy.models import Job, JobPostings
from test_utils.factories import JobFactory
from test_utils.sample_responses.job_postings import JOB_POSTINGS, MISSING_MEDIAN_SALARY_JOB_POSTING
from test_utils.testcase import TaxonomyTestCase


@ddt
@mark.django_db
class RefreshJobPostingsCommandTests(TaxonomyTestCase):
    """
    Test command `refresh_job_postings_data`.
    """

    command = 'refresh_job_postings_data'

    def setUp(self):
        """
        Testcase Setup.
        """
        self.job_postings_data = JOB_POSTINGS
        # creating jobs
        for job_bucket in self.job_postings_data['data']['ranking']['buckets']:
            JobFactory(external_id=job_bucket['name'])
        self.missing_median_salary = MISSING_MEDIAN_SALARY_JOB_POSTING
        self.mock_access_token()
        super(RefreshJobPostingsCommandTests, self).setUp()

    @data(False, True)
    @responses.activate
    @mock.patch('taxonomy.management.commands.refresh_job_skills.EMSIJobsApiClient.get_job_postings')
    def test_job_postings_saved(self, missing_job, get_job_postings_mock):
        """
        Test that the command creates JobPostings.
        """
        get_job_postings_mock.return_value = self.job_postings_data
        jobs_count = Job.objects.count()

        if missing_job:
            # remove one job
            first_job = Job.objects.first()
            Job.objects.filter(external_id=first_job.external_id).delete()

            assert Job.objects.count() == jobs_count - 1
            jobs_count = jobs_count - 1

        self.assertEqual(JobPostings.objects.count(), 0)

        call_command(self.command)

        # asset jobPosting are creating for all the jobs
        self.assertEqual(JobPostings.objects.all().count(), jobs_count)

    @responses.activate
    @mock.patch('taxonomy.management.commands.refresh_job_skills.EMSIJobsApiClient.get_job_postings')
    def test_job_postings_not_saved_upon_exception(self, get_job_postings_mock):
        """
        Test that the command does not create any records when the API throws an exception.
        """
        get_job_postings_mock.side_effect = TaxonomyAPIError()
        jobs = Job.objects.all()
        job_postings = JobPostings.objects.all()
        self.assertEqual(jobs.count(), 3)
        self.assertEqual(job_postings.count(), 0)

        err_string = _('Taxonomy API Error for refreshing the job postings data for Ranking Facet RankingFacet.TITLE')
        with LogCapture(level=logging.INFO) as log_capture:
            with self.assertRaisesRegex(CommandError, err_string):
                call_command(self.command)
            # Validate a descriptive and readable log message.
            self.assertEqual(len(log_capture.records), 1)
            message = log_capture.records[0].msg
            self.assertEqual(
                message,
                'Taxonomy API Error for refreshing the job postings data for Ranking Facet RankingFacet.TITLE'
            )

        self.assertEqual(jobs.count(), 3)
        self.assertEqual(job_postings.count(), 0)

    @responses.activate
    @mock.patch('taxonomy.management.commands.refresh_job_skills.EMSIJobsApiClient.get_job_postings')
    def test_job_postings_not_saved_on_key_error(self, get_job_postings_mock):
        """
        Test that the command does not create any records when a key error occurs.
        """
        get_job_postings_mock.return_value = self.missing_median_salary
        jobs = Job.objects.all()
        job_postings = JobPostings.objects.all()
        self.assertEqual(jobs.count(), 3)
        self.assertEqual(job_postings.count(), 0)

        err_string = _("Missing keys in job postings data. Error: 'median_salary'")
        with LogCapture(level=logging.INFO) as log_capture:
            with self.assertRaisesRegex(CommandError, err_string):
                call_command(self.command)
            # Validate a descriptive and readable log message.
            self.assertEqual(len(log_capture.records), 1)
            message = log_capture.records[0].msg
            self.assertEqual(message, "Missing keys in job postings data. Error: 'median_salary'")

        self.assertEqual(jobs.count(), 3)
        self.assertEqual(job_postings.count(), 0)
