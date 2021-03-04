# -*- coding: utf-8 -*-
"""
Clients for communicating with the EMSI Service.
"""

import logging
from functools import wraps
from time import time

import requests
from edx_rest_api_client.client import EdxRestApiClient
from requests.exceptions import ConnectionError, Timeout  # pylint: disable=redefined-builtin
from slumber.exceptions import SlumberBaseException

from django.conf import settings

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
        self.expires_at = 0

        self.client = EdxRestApiClient(
            self.API_BASE_URL,
            append_slash=self.APPEND_SLASH,
            oauth_access_token=self.oauth_access_token(),
        )

    def oauth_access_token(self, grant_type='client_credentials'):
        """
        Fetch a new access token from EMSI API.

        Arguments:
            grant_type (str): Grant type, usually `client_credentials`
        """
        data = {
            'grant_type': grant_type,
            'client_id': self.client_id,
            'client_secret': self.client_secret
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
            self.expires_at = int(time()) + expires_in
            return access_token

        LOGGER.error('[EMSI Service] Error occurred while getting the access token for EMSI service')
        return None

    def connect(self):
        """
        Connect to the REST API, authenticating with a JWT for the current user.
        """
        self.client = EdxRestApiClient(
            self.API_BASE_URL,
            append_slash=self.APPEND_SLASH,
            oauth_access_token=self.oauth_access_token(),
        )

    def is_token_expired(self):
        """
        Return True if the access token has expired, False if not.
        """
        return int(time()) > self.expires_at

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

    API_BASE_URL = JwtEMSIApiClient.API_BASE_URL + '/skills/versions/7.35'

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
        data = {
            'text': course_text_data
        }
        try:
            response = self.client.extract.post(data)
            return self.traverse_data(response)
        except (SlumberBaseException, ConnectionError, Timeout) as error:
            LOGGER.exception(
                '[TAXONOMY] Exception raised while fetching skills data from EMSI. PostData: [%s]',
                data
            )
            raise TaxonomyAPIError('Error while fetching course skills.') from error

    @staticmethod
    def traverse_data(response):
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

    API_BASE_URL = JwtEMSIApiClient.API_BASE_URL + '/jpa'

    def __init__(self):
        """
        Initialize base class with "postings:us" scope.
        """
        super(EMSIJobsApiClient, self).__init__(scope='postings:us')

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
        url = 'taxonomies/{facet}/lookup'.format(
            facet=ranking_facet.value,
        )
        try:
            endpoint = getattr(self.client, url)
            response = endpoint().post(query_filter)
            return response
        except (SlumberBaseException, ConnectionError, Timeout) as error:
            LOGGER.exception('[TAXONOMY] Exception raised while fetching data from EMSI')
            raise TaxonomyAPIError(
                'Error while fetching lookup for {ranking_facet}'.format(ranking_facet=ranking_facet.value)
            ) from error

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
        url = 'rankings/{ranking_facet}/rankings/{nested_ranking_facet}'.format(
            ranking_facet=ranking_facet.value,
            nested_ranking_facet=nested_ranking_facet.value,
        )
        try:
            endpoint = getattr(self.client, url)
            response = endpoint().post(query_filter)
            return self.traverse_jobs_data(response)
        except (SlumberBaseException, ConnectionError, Timeout) as error:
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
        url = 'rankings/{ranking_facet}'.format(ranking_facet=ranking_facet.value)
        try:
            endpoint = getattr(self.client, url)
            response = endpoint().post(query_filter)
            return self.traverse_job_postings_data(response)
        except (SlumberBaseException, ConnectionError, Timeout) as error:
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
