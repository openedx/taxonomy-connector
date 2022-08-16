# -*- coding: utf-8 -*-
"""
Tests for the `taxonomy-connector` emsi client.
"""

import logging
from time import time

import responses
from pytest import raises
from testfixtures import LogCapture

from taxonomy.emsi.client import EMSIJobsApiClient, EMSISkillsApiClient, JwtEMSIApiClient
from taxonomy.enums import RankingFacet
from taxonomy.exceptions import TaxonomyAPIError
from test_utils.decorators import mock_api_response
from test_utils.sample_responses.job_lookup import JOB_LOOKUP, JOB_LOOKUP_FILTER
from test_utils.sample_responses.job_postings import JOB_POSTINGS, JOB_POSTINGS_FILTER
from test_utils.sample_responses.jobs import JOBS, JOBS_FILTER
from test_utils.sample_responses.skills import (
    SKILL_TEXT_DATA, SKILLS_EMSI_CLIENT_RESPONSE, SKILLS_EMSI_RESPONSE, SKILL_ID, SKILL_DETAILS_EMSI_RESPONSE
)
from test_utils.testcase import TaxonomyTestCase


class TestJwtEMSIApiClient(TaxonomyTestCase):
    """
    Validate that JWT token are fetched and cached appropriately.
    """

    def setUp(self):
        """
        Instantiate an instance of JwtEMSIApiClient for use inside tests.
        """
        super(TestJwtEMSIApiClient, self).setUp()

        self.client = JwtEMSIApiClient(scope='EMSI')

    @mock_api_response(
        method=responses.POST,
        url=JwtEMSIApiClient.ACCESS_TOKEN_URL,
        json={'access_token': 'test-token', 'expires_in': 60}
    )
    def test_get_oauth_access_token(self):
        """
        Validate that `oauth_access_token` correctly handles request to fetch access token.
        """
        token = self.client.oauth_access_token()
        assert token == 'test-token'
        assert self.client.expires_at > 0

    @mock_api_response(
        method=responses.POST,
        url=JwtEMSIApiClient.ACCESS_TOKEN_URL,
        json={'access_token': 'test-token', 'expires_in': 60},
        status=403
    )
    def test_get_oauth_access_token_error(self):
        """
        Validate that `fetch_oauth_access_token` correctly handles errors while fetching access token.
        """
        with LogCapture(level=logging.INFO) as log_capture:
            token = self.client.oauth_access_token()
            assert token is None

            # Validate a descriptive and readable log message.
            assert len(log_capture.records) == 1
            message = log_capture.records[0].msg
            assert message == '[EMSI Service] Error occurred while getting the access token for EMSI service'

    @mock_api_response(
        method=responses.POST,
        url=JwtEMSIApiClient.ACCESS_TOKEN_URL,
        json={'access_token': 'test-token', 'expires_in': 60},
    )
    def test_connect(self):
        """
        Validate that `connect` works.
        """
        self.client.connect()

        # Make sure API call was sent out.
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == JwtEMSIApiClient.ACCESS_TOKEN_URL

    @mock_api_response(
        method=responses.POST,
        url=JwtEMSIApiClient.ACCESS_TOKEN_URL,
        json={'access_token': 'test-token', 'expires_in': 60},
    )
    def test_refresh_token(self):
        """
        Validate that the behavior of refresh_token decorator.
        """
        # set an expiry value
        self.client.expires_at = int(time()) + 60

        # Apply the decorator
        func = self.client.refresh_token(lambda client, *args, **kwargs: None)
        func(self.client)

        # Make sure API call was not sent out.
        assert len(responses.calls) == 0

        # expire the token
        self.client.expires_at = 0
        # Apply the decorator
        func(self.client)

        # Make sure API call was sent out this time.
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == JwtEMSIApiClient.ACCESS_TOKEN_URL


class TestEMSISkillsApiClient(TaxonomyTestCase):
    """
    Validate that course skills are fetched from correct endpoint and with proper authentication.
    """
    def setUp(self):
        """
        Instantiate an instance of EMSISkillsApiClient for use inside tests.
        """
        super(TestEMSISkillsApiClient, self).setUp()
        self.client = EMSISkillsApiClient()
        self.mock_access_token()

    @mock_api_response(
        method=responses.POST,
        url=EMSISkillsApiClient.API_BASE_URL + '/extract',
        json=SKILLS_EMSI_RESPONSE,
    )
    def test_client_error(self):
        """
        Validate that initializing EMSISkillsApiClient does not raise error.
        """
        # Initialize once and call the API
        client = EMSISkillsApiClient()
        skills = client.get_product_skills(SKILL_TEXT_DATA)
        assert skills == SKILLS_EMSI_CLIENT_RESPONSE

        # Initialize the client again to simulate error condition.
        client = EMSISkillsApiClient()
        skills = client.get_product_skills(SKILL_TEXT_DATA)
        assert skills == SKILLS_EMSI_CLIENT_RESPONSE

    @mock_api_response(
        method=responses.POST,
        url=EMSISkillsApiClient.API_BASE_URL + '/extract',
        json=SKILLS_EMSI_RESPONSE,
    )
    def test_get_product_skills(self):
        """
        Validate that the behavior of client while fetching product skills.
        """
        skills = self.client.get_product_skills(SKILL_TEXT_DATA)

        assert skills == SKILLS_EMSI_CLIENT_RESPONSE

    @mock_api_response(
        method=responses.POST,
        url=EMSISkillsApiClient.API_BASE_URL + '/extract',
        json=SKILLS_EMSI_RESPONSE,
        status=400,
    )
    def test_get_product_skills_error(self):
        """
        Validate that the behavior of client when error occurs while fetching skill data.
        """
        with raises(TaxonomyAPIError, match='Error while fetching product skills.'):
            self.client.get_product_skills(SKILL_TEXT_DATA)

    @mock_api_response(
        method=responses.GET,
        url=EMSISkillsApiClient.API_BASE_URL + f'/skills/{SKILL_ID}',
        json=SKILL_DETAILS_EMSI_RESPONSE,
    )
    def test_get_skill_details(self):
        """
        Validate that the behavior of client while fetching product skills.
        """
        skills = self.client.get_skill_details(SKILL_ID)

        assert skills == SKILL_DETAILS_EMSI_RESPONSE

    @mock_api_response(
        method=responses.GET,
        url=EMSISkillsApiClient.API_BASE_URL + f'/skills/{SKILL_ID}',
        json=SKILL_DETAILS_EMSI_RESPONSE,
        status=400,
    )
    def test_get_skill_details_error(self):
        """
        Validate that the behavior of client when error occurs while fetching skill data.
        """
        with raises(TaxonomyAPIError, match='Error while fetching skill details.'):
            self.client.get_skill_details(SKILL_ID)


class TestEMSIJobsApiClient(TaxonomyTestCase):
    """
    Validate that jobs and job postings related data is fetched from correct endpoint with proper authentication.
    """
    def setUp(self):
        """
        Instantiate an instance of EMSISkillsApiClient for use inside tests.
        """
        super(TestEMSIJobsApiClient, self).setUp()
        self.mock_access_token()
        self.client = EMSIJobsApiClient()

    @mock_api_response(
        method=responses.POST,
        url=EMSIJobsApiClient.API_BASE_URL + '/rankings/{}/rankings/{}'.format(
            RankingFacet.TITLE_NAME.value, RankingFacet.SKILLS_NAME.value
        ),
        json=JOBS,
    )
    def test_get_jobs(self):
        """
        Validate that the behavior of client while fetching jobs data.
        """
        jobs = self.client.get_jobs(RankingFacet.TITLE_NAME, RankingFacet.SKILLS_NAME, JOBS_FILTER)

        assert jobs == JOBS

    @mock_api_response(
        method=responses.POST,
        url=EMSIJobsApiClient.API_BASE_URL + '/rankings/{}/rankings/{}'.format(
            RankingFacet.TITLE_NAME.value, RankingFacet.SKILLS_NAME.value
        ),
        json=JOBS,
        status=400,
    )
    def test_get_jobs_error(self):
        """
        Validate that the behavior of client when error occurs while fetching jobs data.
        """
        with raises(
                TaxonomyAPIError,
                match='Error while fetching job rankings for {ranking_facet}/{nested_ranking_facet}.'.format(
                    ranking_facet=RankingFacet.TITLE_NAME.value,
                    nested_ranking_facet=RankingFacet.SKILLS_NAME.value
                )
        ):
            self.client.get_jobs(RankingFacet.TITLE_NAME, RankingFacet.SKILLS_NAME, JOBS_FILTER)

    @mock_api_response(
        method=responses.POST,
        url=EMSIJobsApiClient.API_BASE_URL + '/rankings/{}'.format(RankingFacet.TITLE_NAME.value),
        json=JOB_POSTINGS,
    )
    def test_get_job_postings_data(self):
        """
        Validate that the behavior of client while fetching job postings data.
        """
        job_postings = self.client.get_job_postings(RankingFacet.TITLE_NAME, JOB_POSTINGS_FILTER)

        assert job_postings == JOB_POSTINGS

    @mock_api_response(
        method=responses.POST,
        url=EMSIJobsApiClient.API_BASE_URL + '/rankings/{}'.format(RankingFacet.TITLE_NAME.value),
        json=JOB_POSTINGS,
        status=400,
    )
    def test_get_job_postings_data_error(self):
        """
        Validate that the behavior of client when error occurs while fetching job postings data.
        """
        with raises(
                TaxonomyAPIError,
                match='Error while fetching job postings data ranked by {ranking_facet}.'.format(
                    ranking_facet=RankingFacet.TITLE_NAME.value,
                )
        ):
            self.client.get_job_postings(RankingFacet.TITLE_NAME, JOB_POSTINGS_FILTER)

    @mock_api_response(
        method=responses.POST,
        url=EMSIJobsApiClient.API_BASE_URL + '/taxonomies/{}/lookup'.format(RankingFacet.TITLE.value),
        json=JOB_LOOKUP,
    )
    def test_get_details(self):
        """
        Validate the behavior of client while fetching job lookup data.
        """
        jobs_details = self.client.get_details(RankingFacet.TITLE, JOB_LOOKUP_FILTER)

        assert jobs_details == JOB_LOOKUP

    @mock_api_response(
        method=responses.POST,
        url=EMSIJobsApiClient.API_BASE_URL + '/taxonomies/{}/lookup'.format(RankingFacet.TITLE.value),
        json=JOB_LOOKUP,
        status=400,
    )
    def test_get_details_error(self):
        """
        Validate the behavior of client when error occurs while fetching job lookup data.
        """
        with raises(
                TaxonomyAPIError,
                match='Error while fetching lookup for {ranking_facet}'.format(ranking_facet=RankingFacet.TITLE.value)
        ):
            self.client.get_details(RankingFacet.TITLE, JOB_LOOKUP_FILTER)
