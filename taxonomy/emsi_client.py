# -*- coding: utf-8 -*-
"""
Clients for communicating with the EMSI Service.
"""

import logging
from functools import wraps

import requests
from edx_django_utils.cache import TieredCache, get_cache_key
from edx_rest_api_client.client import EdxRestApiClient
from requests.exceptions import ConnectionError, Timeout  # pylint: disable=redefined-builtin
from slumber.exceptions import SlumberBaseException

from django.conf import settings

from taxonomy.constants import JOB_POSTINGS_QUERY_FILTER, JOBS_QUERY_FILTER
from taxonomy.exceptions import TaxonomyAPIError

LOGGER = logging.getLogger(__name__)


class JwtEMSIApiClient:
    """
    EMSI client authenticates using a access token for the given user.
    """

    ACCESS_TOKEN_URL = settings.EMSI_API_ACCESS_TOKEN_URL
    API_BASE_URL = settings.EMSI_API_BASE_URL
    APPEND_SLASH = False

    client_id = settings.EMSI_CLIENT_ID
    client_secret = settings.EMSI_CLIENT_SECRET

    def __init__(self, scope):
        """
        Initialize the instance with arguments provided or default values otherwise.

        Arguments:
            scope (str): The value of the scope depends on the EMSI API endpoints we want to
                access and its values are dependant on EMSI API specifications. Example values
                are `emsi_open` and `postings:us`.
        """
        self.scope = scope

        self.client = EdxRestApiClient(
            self.API_BASE_URL,
            append_slash=self.APPEND_SLASH,
            oauth_access_token=self.access_token,
        )

    @property
    def cache_key(self):
        """
        Return the cache key, caching is done based on the endpoint name and the scope property.
        """
        return get_cache_key(endpoint='EMSI', scope=self.scope)

    def fetch_oauth_access_token(self, client_id, client_secret, grant_type='client_credentials'):
        """
        Fetch a new access token from EMSI API. This method will also cache the new access token fetched from the API.

        Arguments:
            client_id (str): Client id provided by the EMSI API Service.
            client_secret (str): Client secret provided by the EMSI API Service.
            grant_type (str): Grant type, usually `client_credentials`
        """
        data = {
            'grant_type': grant_type,
            'client_id': client_id,
            'client_secret': client_secret
        }

        response = requests.post(
            self.ACCESS_TOKEN_URL,
            data=data,
            headers={'content-type': 'application/x-www-form-urlencoded'}
        )

        if response.ok:
            data = response.json()
            access_token = data['access_token']
            expires_in = data['expires_in']
            TieredCache.set_all_tiers(self.cache_key, access_token, expires_in)
            return access_token

        LOGGER.error('[EMSI Service] Error occurred while getting the access token for EMSI service')
        return None

    @property
    def access_token(self):
        """
        Get and return the access token for EMSI API access.

        The property method will try these steps in order to get the access token.
            1. Find and return the access token from the cache
            2. If cache is empty, then fetch and return a new access token using EMSI API.

        Returns:
            (str|None): Access token or `None` if access could not be found from the cache and the API did not return
                a successful response.
        """
        cached_response = TieredCache.get_cached_response(self.cache_key)
        if cached_response.is_found:
            return cached_response.value

        access_token = self.fetch_oauth_access_token(
            client_id=self.client_id,
            client_secret=self.client_secret,
        )
        return access_token

    def connect(self):
        """
        Connect to the REST API, authenticating with a JWT for the current user.
        """
        self.client = EdxRestApiClient(
            self.API_BASE_URL,
            append_slash=self.APPEND_SLASH,
            oauth_access_token=self.access_token,
        )

    def is_token_expired(self):
        """
        Return True if the access token has expired, False if not.
        """
        cached_response = TieredCache.get_cached_response(self.cache_key)
        return not cached_response.is_found

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


class EMSISkillsApiClient(JwtEMSIApiClient):
    """
    Object builds an API client to make calls to get the skills from course text data.
    """

    API_BASE_URL = JwtEMSIApiClient.API_BASE_URL + '/skills'

    def __init__(self):
        """
        Initialize base class with `emsi_open` scope.
        """
        super(EMSISkillsApiClient, self).__init__(scope='emsi_open')

    @JwtEMSIApiClient.refresh_token
    def get_course_skills(self, course_text_data):
        """
        Query the EMSI API for the skills of the given course text data.

        Arguments:
            course_text_data (str): Course data as text, this is usually the course description.

        Returns:
            dict: A dictionary containing details of all the skills.
        """
        try:
            data = {
                'text': course_text_data
            }
            response = self.client.versions.latest.extract.post(data)

            return self.traverse_data(response)
        except (SlumberBaseException, ConnectionError, Timeout) as error:
            raise TaxonomyAPIError('Error while fetching course skills.') from error

    @staticmethod
    def traverse_data(response):
        """
        Transform data to a more useful format.
        """
        return response


class EMSIJobsApiClient(JwtEMSIApiClient):
    """
    Object builds an API client to make calls to get the Jobs.
    """

    API_BASE_URL = JwtEMSIApiClient.API_BASE_URL + '/jpa'

    def __init__(self):
        """
        Initialize base class with "postings:us" scope.
        """
        super(EMSIJobsApiClient, self).__init__(scope='postings:us')

    @JwtEMSIApiClient.refresh_token
    def get_jobs(self, ranking_facet, nested_ranking_facet, query_filter=None):
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
        url = 'rankings/{ranking_facet}/rankings/{nested_ranking_facet}'.format(
            ranking_facet=ranking_facet.value,
            nested_ranking_facet=nested_ranking_facet.value,
        )
        query_filter = query_filter if query_filter else JOBS_QUERY_FILTER
        try:
            endpoint = getattr(self.client, url)
            response = endpoint().post(query_filter)
            return self.traverse_jobs_data(response)
        except (SlumberBaseException, ConnectionError, Timeout) as error:
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

    @JwtEMSIApiClient.refresh_token
    def get_job_postings(self, ranking_facet, query_filter=None):
        """
        Query the EMSI API for the job postings data of the pre-defined filter_query.

        Arguments:
            ranking_facet (RankingFacet): Data will be ranked by this facet.
            query_filter (dict): Filters to be sent in the POST data.

        Returns:
            dict: A dictionary containing job postings data.
        """
        url = 'rankings/{ranking_facet}'.format(ranking_facet=ranking_facet.value)
        query_filter = query_filter if query_filter else JOB_POSTINGS_QUERY_FILTER
        try:
            endpoint = getattr(self.client, url)
            response = endpoint().post(query_filter)
            return self.traverse_job_postings_data(response)
        except (SlumberBaseException, ConnectionError, Timeout) as error:
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
