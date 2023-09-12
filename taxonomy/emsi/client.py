# -*- coding: utf-8 -*-
"""
Clients for communicating with the EMSI Service.
"""

import logging
from functools import wraps
from time import time, sleep
from urllib.parse import urljoin

import requests
from edx_rest_api_client.auth import BearerAuth
from requests.adapters import HTTPAdapter
from requests.exceptions import ConnectionError, RequestException, Timeout  # pylint: disable=redefined-builtin
from urllib3 import Retry

from django.conf import settings

from taxonomy.exceptions import TaxonomyAPIError
from taxonomy.constants import EMSI_API_RATE_LIMIT_PER_SEC

LOGGER = logging.getLogger(__name__)


class JwtEMSIApiClient:
    """
    EMSI client authenticates using a access token for the given user.
    """
    REQUEST_COUNT_CACHE = {}

    ACCESS_TOKEN_URL = settings.EMSI_API_ACCESS_TOKEN_URL
    API_BASE_URL = settings.EMSI_API_BASE_URL
    APPEND_SLASH = False

    client_id = settings.EMSI_CLIENT_ID
    client_secret = settings.EMSI_CLIENT_SECRET
    ACCESS_TOKEN_EXPIRY_THRESHOLD = 60

    def __init__(self, scope):
        """
        Initialize the instance with arguments provided or default values otherwise.

        Arguments:
            scope (str): The value of the scope depends on the EMSI API endpoints we want to
                access and its values are dependent on EMSI API specifications. Example values
                are `emsi_open` and `postings:us`.
        """
        self.scope = scope
        self.expires_at = 0
        self.client = None

    @classmethod
    def __ensure_request_allowed(cls):
        """
        Ensure the request to LightCast API is allowed.

        This function will first check the total number of requests to the LightCast API in the current second,
        - If the rate limit is reached then it will wait for 1 second and start the counter from 0.
        - If the rate limit is not reached it will simply update the counter.
        It also makes sure to clear the dict for the past (redundant) entries to avoid dict size from
        increasing put of bound.
        """
        # Wait for a second if limit for the current second is reached.
        if cls.REQUEST_COUNT_CACHE.get(int(time()), 0) > EMSI_API_RATE_LIMIT_PER_SEC:
            sleep(1)

        second_count = int(time())

        # If a second has passed then clear the dict and start counting from the start.
        if second_count not in cls.REQUEST_COUNT_CACHE:
            cls.REQUEST_COUNT_CACHE.clear()
            cls.REQUEST_COUNT_CACHE[second_count] = 0

        cls.REQUEST_COUNT_CACHE[second_count] += 1

    @staticmethod
    def handle_rate_limiting(func):
        """
        Handle rate limiting restrictions by LightCast.

        Currently, LightCast enforces 5 requests/second per client. This decorator tries to avoid rate limiting errors.
        """

        @wraps(func)
        def inner(*args, **kwargs):
            """
            Before calling the wrapped function, we check if we have exhausted the rate limit set by LightCast API.
            """
            # Ensure the rate limit is not reached before calling the decorated function.
            JwtEMSIApiClient.__ensure_request_allowed()
            return func(*args, **kwargs)

        return inner

    def oauth_access_token(self, grant_type='client_credentials'):
        """
        Fetch a new access token from EMSI API.

        Arguments:
            grant_type (str): Grant type, usually `client_credentials`
        """
        data = {
            'grant_type': grant_type,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': self.scope,
        }

        # Make sure to avoid rate limit.
        self.__ensure_request_allowed()
        response = requests.post(
            self.ACCESS_TOKEN_URL,
            data=data,
            headers={'content-type': 'application/x-www-form-urlencoded'}
        )

        if not response.ok:
            LOGGER.error(
                '[EMSI Service] Error occurred while getting the access token for EMSI service. Response: %s',
                response.__dict__
            )
            response.raise_for_status()

        LOGGER.info('[EMSI Service] Access token fetched successfully.')
        data = response.json()
        access_token = data['access_token']
        expires_in = data['expires_in']
        self.expires_at = int(time()) + expires_in
        return access_token

    def connect(self):
        """
        Connect to the REST API, authenticating with a JWT for the current user.
        """
        self.client = requests.Session()
        self.client.auth = BearerAuth(self.oauth_access_token())
        adapter = HTTPAdapter(
            max_retries=Retry(
                total=3, backoff_factor=1, allowed_methods=None, status_forcelist=[429]
            )
        )
        self.client.mount("http://", adapter)
        self.client.mount("https://", adapter)

    def is_token_expired(self):
        """
        Return True if the access token has expired, False if not.
        """
        expires_at = self.expires_at - self.ACCESS_TOKEN_EXPIRY_THRESHOLD
        return int(time()) > expires_at

    @staticmethod
    def refresh_token(func):
        """
        Use this method decorator to ensure the access token is refreshed when needed.
        """
        @wraps(func)
        def inner(self, *args, **kwargs):
            """
            Before calling the wrapped function, we check if the access token is expired, and if so, re-connect.
            """
            if self.is_token_expired():
                self.connect()
            return func(self, *args, **kwargs)
        return inner

    def get_api_url(self, path):
        """
        Construct the full API URL using the API_BASE_URL and path.
        Args:
            path (str): API endpoint path.
        """
        path = path.strip('/')
        if self.APPEND_SLASH:
            path += '/'

        return urljoin(f"{self.API_BASE_URL}/", path)


class EMSISkillsApiClient(JwtEMSIApiClient):
    """
    Object builds an API client to make calls to get the skills from course text data.
    """

    API_BASE_URL = urljoin(JwtEMSIApiClient.API_BASE_URL, '/skills/versions/8.9')
    MAX_LIGHTCAST_DATA_SIZE = 50000  # Maximum 50,000-byte data is supported by LightCast

    def __init__(self):
        """
        Initialize base class with `emsi_open` scope.
        """
        super(EMSISkillsApiClient, self).__init__(scope='emsi_open')

    @JwtEMSIApiClient.handle_rate_limiting
    @JwtEMSIApiClient.refresh_token
    def get_skill_details(self, skill_id):
        """
        Query the EMSI API to get details for a particular skill.

        We will be using this method to populate skill category and subcategory.

        Arguments:
             skill_id (str): Skill external id, this is the id that comes from EMSI. example: 'KS124P772D5HNCJGGQ05'

        Returns:
            (dict): A dictionary containing the skill details.
        """
        try:
            api_url = self.get_api_url(f'skills/{skill_id}')
            response = self.client.get(api_url)
            response.raise_for_status()
            return response.json()
        except (RequestException, ConnectionError, Timeout) as error:
            LOGGER.exception(
                '[TAXONOMY] Exception raised while fetching skill details from EMSI. Skill ID: [%s]',
                skill_id
            )
            raise TaxonomyAPIError('Error while fetching skill details.') from error

    @JwtEMSIApiClient.handle_rate_limiting
    @JwtEMSIApiClient.refresh_token
    def get_product_skills(self, text_data):
        """
        Query the EMSI API for the skills of the given product text data.

        Arguments:
            text_data (str): Product data as text, this is usually description in case of a course
            or overview in case of a program.

        Returns:
            dict: A dictionary containing details of all the skills.
        """

        if text_data and len(text_data) > self.MAX_LIGHTCAST_DATA_SIZE:
            # Truncate the text_data to 50,000 bytes since only 50,000-byte data is supported by LightCast
            text_data = text_data[:self.MAX_LIGHTCAST_DATA_SIZE]

        data = {
            'text': text_data
        }
        try:
            api_url = self.get_api_url('extract')
            response = self.client.post(
                api_url,
                json=data,
            )
            response.raise_for_status()
            return self.traverse_skills_data(response.json())
        except (RequestException, ConnectionError, Timeout) as error:
            LOGGER.exception(
                '[TAXONOMY] Exception raised while fetching skills data from EMSI. PostData: [%s]',
                data
            )
            raise TaxonomyAPIError('Error while fetching product skills.') from error

    @staticmethod
    def traverse_skills_data(response):
        """
        Transform data to a more useful format.
        """
        for skill_details in response['data']:
            # append skill description in skill data extracted from "wikipediaExtract" tag
            try:
                desc = next(tag['value'] for tag in skill_details['skill']['tags'] if tag['key'] == 'wikipediaExtract')
            except StopIteration:
                LOGGER.warning('[TAXONOMY] "wikipediaExtract" key not found in skill: %s', skill_details['skill']['id'])
                desc = ''
            skill_details['skill']['description'] = desc

        return response


class EMSIJobsApiClient(JwtEMSIApiClient):
    """
    Object builds an API client to make calls to get the Jobs.
    """

    API_BASE_URL = urljoin(JwtEMSIApiClient.API_BASE_URL, '/jpa')

    def __init__(self):
        """
        Initialize base class with "postings:us" scope.
        """
        super(EMSIJobsApiClient, self).__init__(scope='postings:us')

    @JwtEMSIApiClient.handle_rate_limiting
    @JwtEMSIApiClient.refresh_token
    def get_details(self, ranking_facet, query_filter):
        """
        Query the EMSI API for the lookup of the pre-defined filter_query.

        Arguments:
            ranking_facet (RankingFacet): Data will be fetched for this facet.
            query_filter (dict): Filters to be sent in the POST data.

        Returns:
            dict: A dictionary containing all the details for given facet.

        """
        try:
            api_url = self.get_api_url(f'taxonomies/{ranking_facet.value}/lookup')
            response = self.client.post(
                api_url,
                json=query_filter,
            )
            response.raise_for_status()
            return response.json()
        except (RequestException, ConnectionError, Timeout) as error:
            LOGGER.exception('[TAXONOMY] Exception raised while fetching data from EMSI')
            raise TaxonomyAPIError(
                'Error while fetching lookup for {ranking_facet}'.format(ranking_facet=ranking_facet.value)
            ) from error

    @JwtEMSIApiClient.handle_rate_limiting
    @JwtEMSIApiClient.refresh_token
    def get_jobs(self, ranking_facet, nested_ranking_facet, query_filter):
        """
        Query the EMSI API for the jobs of the pre-defined filter_query.

        Arguments:
            ranking_facet (RankingFacet): Data will be ranked by this facet.
            nested_ranking_facet (RankingFacet): This is the nested facet to be applied after ranking data by the
                `ranking_facet`.
            query_filter (dict): Filters to be sent in the POST data.

        Returns:
            dict: A dictionary containing details of all the jobs.
        """
        try:
            api_url = self.get_api_url(f'rankings/{ranking_facet.value}/rankings/{nested_ranking_facet.value}')
            response = self.client.post(
                api_url,
                json=query_filter,
            )
            response.raise_for_status()
            return self.traverse_jobs_data(response.json())
        except (RequestException, ConnectionError, Timeout) as error:
            LOGGER.exception('[TAXONOMY] Exception raised while fetching jobs data from EMSI')
            raise TaxonomyAPIError(
                'Error while fetching job rankings for {ranking_facet}/{nested_ranking_facet}.'.format(
                    ranking_facet=ranking_facet.value,
                    nested_ranking_facet=nested_ranking_facet.value,
                )
            ) from error

    @staticmethod
    def traverse_jobs_data(jobs_data):
        """
        Transform data to a more useful format.
        """
        return jobs_data

    @JwtEMSIApiClient.handle_rate_limiting
    @JwtEMSIApiClient.refresh_token
    def get_job_postings(self, ranking_facet, query_filter):
        """
        Query the EMSI API for the job postings data of the pre-defined filter_query.

        Arguments:
            ranking_facet (RankingFacet): Data will be ranked by this facet.
            query_filter (dict): Filters to be sent in the POST data.

        Returns:
            dict: A dictionary containing job postings data.
        """
        try:
            api_url = self.get_api_url(f'rankings/{ranking_facet.value}')
            response = self.client.post(
                api_url,
                json=query_filter,
            )
            response.raise_for_status()
            return self.traverse_job_postings_data(response.json())
        except (RequestException, ConnectionError, Timeout) as error:
            LOGGER.exception('[TAXONOMY] Exception raised while fetching job posting data from EMSI')
            raise TaxonomyAPIError(
                'Error while fetching job postings data ranked by {ranking_facet}.'.format(
                    ranking_facet=ranking_facet.value,
                )
            ) from error

    @staticmethod
    def traverse_job_postings_data(data):
        """
        Transform data to a more useful format.
        """
        return data
