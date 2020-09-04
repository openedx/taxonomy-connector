# -*- coding: utf-8 -*-
"""
Tests for the `taxonomy-service` emsi client.
"""

import logging
import responses

from testfixtures import LogCapture
from edx_django_utils.cache import TieredCache

from test_utils.testcase import TaxonomyTestCase
from taxonomy.emsi_client import JwtEMSIApiClient, EMSISkillsApiClient, EMSIJobsApiClient
from test_utils.constants import CLIENT_ID, CLIENT_SECRET
from test_utils.decorators import mock_api_response
from test_utils.sample_responses.skills import SKILLS, SKILL_TEXT_DATA
from test_utils.sample_responses.jobs import JOBS, JOBS_FILTER
from test_utils.sample_responses.salaries import SALARIES, SALARIES_FILTER


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
        Validate that `get_oauth_access_token` correctly handles request to fetch access token.
        """
        token = self.client.get_oauth_access_token(CLIENT_ID, CLIENT_SECRET)
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
        Validate that `get_oauth_access_token` correctly handles errors while fetching access token.
        """
        with LogCapture(level=logging.INFO) as log_capture:
            token = self.client.get_oauth_access_token(CLIENT_ID, CLIENT_SECRET)
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
        url=EMSISkillsApiClient.API_BASE_URL + '/versions/latest/skills/extract',
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
        url=EMSISkillsApiClient.API_BASE_URL + '/versions/latest/skills/extract',
        json=SKILLS,
        status=400,
    )
    def test_get_course_skills_error(self):
        """
        Validate that the behavior of client when error occurs while fetching skill data.
        """
        skills = self.client.get_course_skills(SKILL_TEXT_DATA)

        assert skills == {}


class TestEMSIJobsApiClient(TaxonomyTestCase):
    """
    Validate that jobs and salary related data is fetched from correct endpoint with proper authentication.
    """
    def setUp(self):
        """
        Instantiate an instance of EMSISkillsApiClient for use inside tests.
        """
        super(TestEMSIJobsApiClient, self).setUp()
        self.client = EMSIJobsApiClient()
        self.mock_access_token()

    def tearDown(self):
        """
        Clear out the cache.
        """
        super(TestEMSIJobsApiClient, self).tearDown()
        TieredCache.dangerous_clear_all_tiers()

    @mock_api_response(
        method=responses.POST,
        url=EMSIJobsApiClient.API_BASE_URL + '/rankings/title_name/rankings/skills_name',
        json=JOBS,
    )
    def test_get_jobs(self):
        """
        Validate that the behavior of client while fetching jobs data.
        """
        jobs = self.client.get_jobs(JOBS_FILTER)

        assert jobs == JOBS

    @mock_api_response(
        method=responses.POST,
        url=EMSIJobsApiClient.API_BASE_URL + '/rankings/title_name/rankings/skills_name',
        json=JOBS,
        status=400,
    )
    def test_get_jobs_error(self):
        """
        Validate that the behavior of client when error occurs while fetching jobs data.
        """
        jobs = self.client.get_jobs(JOBS_FILTER)

        assert jobs == {}

    @mock_api_response(
        method=responses.POST,
        url=EMSIJobsApiClient.API_BASE_URL + '/rankings/title_name',
        json=SALARIES,
    )
    def test_get_salaries(self):
        """
        Validate that the behavior of client while fetching jobs data.
        """
        salaries = self.client.get_salaries(SALARIES_FILTER)

        assert salaries == SALARIES

    @mock_api_response(
        method=responses.POST,
        url=EMSIJobsApiClient.API_BASE_URL + '/rankings/title_name',
        json=SALARIES,
        status=400,
    )
    def test_get_salaries_error(self):
        """
        Validate that the behavior of client when error occurs while fetching jobs data.
        """
        salaries = self.client.get_salaries(SALARIES_FILTER)

        assert salaries == {}
