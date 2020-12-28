# -*- coding: utf-8 -*-
"""
Tests for the `taxonomy-connector` emsi client.
"""

import logging

import responses
from edx_django_utils.cache import TieredCache
from pytest import raises
from testfixtures import LogCapture

from taxonomy.emsi_client import EMSIJobsApiClient, EMSISkillsApiClient, JwtEMSIApiClient
from taxonomy.enums import RankingFacet
from taxonomy.exceptions import TaxonomyAPIError
from test_utils.constants import CLIENT_ID, CLIENT_SECRET
from test_utils.decorators import mock_api_response
from test_utils.sample_responses.job_postings import JOB_POSTINGS, JOB_POSTINGS_FILTER
from test_utils.sample_responses.jobs import JOBS, JOBS_FILTER
from test_utils.sample_responses.skills import SKILL_TEXT_DATA, SKILLS
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

    def tearDown(self):
        """
        Clear out the cache.
        """
        super(TestJwtEMSIApiClient, self).tearDown()
        TieredCache.dangerous_clear_all_tiers()

    @mock_api_response(
        method=responses.POST,
        url=JwtEMSIApiClient.ACCESS_TOKEN_URL,
        json={'access_token': 'test-token', 'expires_in': 60}
    )
    def test_get_oauth_access_token(self):
        """
        Validate that `fetch_oauth_access_token` correctly handles request to fetch access token.
        """
        token = self.client.fetch_oauth_access_token(CLIENT_ID, CLIENT_SECRET)
        assert token == 'test-token'

        # Validate that token is also set in the cache
        cached_token = TieredCache.get_cached_response(self.client.cache_key)
        assert cached_token.value == 'test-token'

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
            token = self.client.fetch_oauth_access_token(CLIENT_ID, CLIENT_SECRET)
            assert token is None

            # Validate that token is not set in the cache either
            cached_token = TieredCache.get_cached_response(self.client.cache_key)
            assert not cached_token.is_found

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
        Validate that a new token is only fetched if one is not found in the cache.
        """
        # Add a sample token value in the cache
        TieredCache.set_all_tiers(self.client.cache_key, 'test-token', 60)

        self.client.connect()

        # Make sure API call was not sent out.
        assert len(responses.calls) == 0

        # Remove cached entry and make sure token is then fetched via API call.
        TieredCache.dangerous_clear_all_tiers()
        self.client.connect()

        # Make sure API call was sent out this time.
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
        # Add a sample token value in the cache
        TieredCache.set_all_tiers(self.client.cache_key, 'test-token', 60)

        # Apply the decorator
        func = self.client.refresh_token(lambda client, *args, **kwargs: None)
        func(self.client)

        # Make sure API call was not sent out.
        assert len(responses.calls) == 0

        # Remove cached entry to simulate token expiry.
        TieredCache.dangerous_clear_all_tiers()
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

    def tearDown(self):
        """
        Clear out the cache.
        """
        super(TestEMSISkillsApiClient, self).tearDown()
        TieredCache.dangerous_clear_all_tiers()

    @mock_api_response(
        method=responses.POST,
        url=EMSISkillsApiClient.API_BASE_URL + '/versions/latest/extract',
        json=SKILLS,
    )
    def test_client_error(self):
        """
        Validate that initializing EMSISkillsApiClient does not raise error.
        """
        # Initialize once and call the API
        client = EMSISkillsApiClient()
        skills = client.get_course_skills(SKILL_TEXT_DATA)
        assert skills == SKILLS

        # Initialize the client again to simulate error condition.
        client = EMSISkillsApiClient()
        skills = client.get_course_skills(SKILL_TEXT_DATA)
        assert skills == SKILLS

    @mock_api_response(
        method=responses.POST,
        url=EMSISkillsApiClient.API_BASE_URL + '/versions/latest/extract',
        json=SKILLS,
    )
    def test_get_course_skills(self):
        """
        Validate that the behavior of client while fetching course skills.
        """
        skills = self.client.get_course_skills(SKILL_TEXT_DATA)

        assert skills == SKILLS

    @mock_api_response(
        method=responses.POST,
        url=EMSISkillsApiClient.API_BASE_URL + '/versions/latest/extract',
        json=SKILLS,
        status=400,
    )
    def test_get_course_skills_error(self):
        """
        Validate that the behavior of client when error occurs while fetching skill data.
        """
        with raises(TaxonomyAPIError, match='Error while fetching course skills.'):
            self.client.get_course_skills(SKILL_TEXT_DATA)


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

    def tearDown(self):
        """
        Clear out the cache.
        """
        super(TestEMSIJobsApiClient, self).tearDown()
        TieredCache.dangerous_clear_all_tiers()

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
