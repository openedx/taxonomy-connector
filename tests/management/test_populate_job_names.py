# -*- coding: utf-8 -*-
"""
Tests for the django management command `populate_job_names`.
"""

import logging

import mock
import responses
from ddt import ddt
from pytest import mark
from testfixtures import LogCapture

from django.core.management import CommandError, call_command

from taxonomy.exceptions import TaxonomyAPIError
from taxonomy.models import Job
from test_utils.factories import JobFactory
from test_utils.sample_responses.job_lookup import JOB_LOOKUP, JOB_LOOKUP_MISSING_KEY
from test_utils.testcase import TaxonomyTestCase


@ddt
@mark.django_db
class UpdateJobNamesCommandTests(TaxonomyTestCase):
    """
    Test command `populate_job_names`.
    """

    command = 'populate_job_names'

    def setUp(self):
        """
        Testcase Setup.
        """
        self.job_lookup_response = JOB_LOOKUP
        # creating jobs without names
        for job_bucket in self.job_lookup_response['data']:
            Job.objects.create(external_id=job_bucket['id'])

        self.missing_key_job_lookup_response = JOB_LOOKUP_MISSING_KEY
        self.mock_access_token()
        super(UpdateJobNamesCommandTests, self).setUp()

    @responses.activate
    @mock.patch('taxonomy.management.commands.refresh_job_skills.EMSIJobsApiClient.get_details')
    def test_job_postings_saved(self, get_details_mock):
        """
        Test that the command updates.
        """
        # creating job with name
        job_with_name = JobFactory(external_id='test_id', name="test_name")
        job_with_name_modified_on = job_with_name.modified

        get_details_mock.return_value = self.job_lookup_response

        all_jobs = Job.objects.all()
        jobs_without_name = Job.objects.filter(name='')

        self.assertEqual(all_jobs.count(), 3)
        self.assertEqual(jobs_without_name.count(), 2)

        call_command(self.command)

        # asset Job are updated with names
        self.assertEqual(jobs_without_name.count(), 0)
        self.assertEqual(all_jobs.count(), 3)

        # asset the existing job with name is not updated.
        job_with_name.refresh_from_db()
        self.assertEqual(job_with_name.modified, job_with_name_modified_on)

    @responses.activate
    @mock.patch('taxonomy.management.commands.refresh_job_skills.EMSIJobsApiClient.get_details')
    def test_job_postings_not_saved_upon_exception(self, get_details_mock):
        """
        Test that the command does not create any records when the API throws an exception.
        """
        get_details_mock.side_effect = TaxonomyAPIError("API ERROR")
        jobs_without_name = Job.objects.filter(name='')
        self.assertEqual(jobs_without_name.count(), 2)

        err_string = 'Taxonomy API Error for updating the jobs for Ranking Facet RankingFacet.TITLE Error: API ERROR.'
        with LogCapture(level=logging.INFO) as log_capture:
            with self.assertRaisesRegex(CommandError, err_string):
                call_command(self.command)
            # Validate a descriptive and readable log message.
            self.assertEqual(len(log_capture.records), 2)
            message = log_capture.records[-1].msg
            self.assertEqual(message, err_string)

        self.assertEqual(jobs_without_name.count(), 2)

    @responses.activate
    @mock.patch('taxonomy.management.commands.refresh_job_skills.EMSIJobsApiClient.get_details')
    def test_job_postings_not_saved_on_key_error(self, get_details_mock):
        """
        Test that the command does not create any records when a key error occurs.
        """
        get_details_mock.return_value = self.missing_key_job_lookup_response
        jobs_without_name = Job.objects.filter(name='')
        self.assertEqual(jobs_without_name.count(), 2)

        err_string = 'Missing keys in update Job names. Error: "singular_name".'
        with LogCapture(level=logging.INFO) as log_capture:
            with self.assertRaisesRegex(CommandError, err_string):
                call_command(self.command)
            # Validate a descriptive and readable log message.
            self.assertEqual(len(log_capture.records), 2)
            message = log_capture.records[-1].msg
            self.assertEqual(message, err_string)

        self.assertEqual(jobs_without_name.count(), 2)
