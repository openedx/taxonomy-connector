
import logging
from functools import wraps

from requests.exceptions import ConnectionError, Timeout  # pylint: disable=redefined-builtin
from slumber.exceptions import SlumberBaseException
import requests
from edx_rest_api_client.client import EdxRestApiClient
from edx_django_utils.cache import get_cache_key, TieredCache

logger = logging.getLogger(__name__)


JOBS_QUERY_FILTER = {
    "filter": {
        "when": {
            "start": "2020-01",
            "end": "2020-06",
            "type": "active"
        },
        "posting_duration": {
            "lower_bound": 0,
            "upper_bound": 90
        }
    },
    "rank": {
        "by": "unique_postings",
        "min_unique_postings": 1000,
        "limit": 20
    },
    "nested_rank": {
        "by": "significance",
        "limit": 10
    }
}

SALARIES_QUERY_FILTER = {
    "filter": {
        "when": {
            "start": "2020-01",
            "end": "2020-06",
            "type": "active"
        },
        "posting_duration": {
            "lower_bound": 0,
            "upper_bound": 90
        }
    },
    "rank": {
        "by": "unique_postings",
        "min_unique_postings": 1000,
        "limit": 20,
        "extra_metrics": [
            "median_posting_duration",
            "median_salary",
            "unique_companies"
        ]
    }
}


class JwtEMSIApiClient(object):
    """
    EMSI client authenticates using a access token for the given user.
    """
    ACCESS_TOKEN_URL = "https://auth.emsicloud.com/connect/token"
    API_BASE_URL = "https://emsiservices.com"
    APPEND_SLASH = False

    def __init__(self, scope):
        """
        Connect to the REST API.
        """
        self.client = None
        self.scope = scope

    @property
    def cache_key(self):
        """
        Return the cache key
        """
        return get_cache_key(endpoint="EMSI", scope=self.scope)

    def get_oauth_access_token(self, client_id, client_secret, grant_type='client_credentials'):
        """
        Return the access token if its cache otherwise hit the endpoint to get the new access token.
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

        logger.error('[EMSI Service] Error occurred while getting the access token for EMSI service')

    def connect(self):
        """
        Connect to the REST API, authenticating with a JWT for the current user.
        """
        access_token = None
        cached_response = TieredCache.get_cached_response(self.cache_key)
        if cached_response.is_found:
            access_token = cached_response.value

        if access_token is None:
            access_token = self.get_oauth_access_token(
                client_id='edx',
                client_secret='vZHeB5Je'
            )

        self.client = EdxRestApiClient(
            self.API_BASE_URL,
            append_slash=self.APPEND_SLASH,
            oauth_access_token=access_token,
        )

    def token_expired(self):
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
            if self.token_expired():
                self.connect()
            return func(self, *args, **kwargs)
        return inner


class EMSISkillsApiClient(JwtEMSIApiClient):
    """
    Object builds an API client to make calls to get the skills from course text data.
    """
    API_BASE_URL = "https://emsiservices.com/skills"

    def __init__(self):
        super(EMSISkillsApiClient, self).__init__(scope="emsi_open")

    @JwtEMSIApiClient.refresh_token
    def get_course_skills(self, course_text_data):
        """
        Query the EMSI API for the skills of the given course text data.

        Args:
            course_text_data (str): The string value of the course text data.

        Returns:
            dict: A dictionary containing details of all the skills.
        """
        try:
            data = {
                "text": course_text_data
            }
            response = self.client.versions.latest.skills.extract.post(data)

            return self.traverse_data(response)
        except (SlumberBaseException, ConnectionError, Timeout) as exc:
            return {}

    @staticmethod
    def traverse_data(data):
        # TODO need to implement this function.
        return data


class EMSIJobsApiClient(JwtEMSIApiClient):
    """
    Object builds an API client to make calls to get the Jobs.
    """
    API_BASE_URL = "https://emsiservices.com/jpa"

    def __init__(self):
        super(EMSIJobsApiClient, self).__init__(scope="postings:us")

    @JwtEMSIApiClient.refresh_token
    def get_jobs(self, query_filter=None):
        """
        Query the EMSI API for the jobs of the pre-defined filter_query.

        Args:
            query_filter (dict): The dictionary of filters.

        Returns:
            dict: A dictionary containing details of all the jobs.
        """
        query_filter = query_filter if query_filter else JOBS_QUERY_FILTER
        try:
            response = self.client.rankings.title_name.rankings.skills_name.post(query_filter)
            return self.traverse_jobs_data(response)
        except (SlumberBaseException, ConnectionError, Timeout) as exc:
            return {}

    @staticmethod
    def traverse_jobs_data(jobs_data):
        # TODO need to implement this function.
        return jobs_data

    @JwtEMSIApiClient.refresh_token
    def get_salaries(self, query_filter=None):
        """
        Query the EMSI API for the salaries of the pre-defined filter_query.

        Args:
            query_filter (dict): The dictionary of filters.

        Returns:
            dict: A dictionary containing details of all the salaries.
        """
        query_filter = query_filter if query_filter else SALARIES_QUERY_FILTER
        try:
            response = self.client.rankings.title_name.post(query_filter)
            return self.traverse_salary_data(response)
        except (SlumberBaseException, ConnectionError, Timeout) as exc:
            return {}

    @staticmethod
    def traverse_salary_data(data):
        # TODO need to implement this function.
        return data
