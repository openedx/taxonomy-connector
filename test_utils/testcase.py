"""
Base test case for taxnomy tests.
"""

import unittest
import responses
from taxonomy.emsi_client import JwtEMSIApiClient


class TaxonomyTestCase(unittest.TestCase):
    """
    Base class for all taxonomy tests.

    If there is functionality common to all tests then either add a mixin or add it here.
    """

    @staticmethod
    def mock_access_token(access_token='test-token', expires_in=60):
        """
        Mock out the access token API endpoint.

        Note: This method is useful in conjunction with one of the decortors applied to the test case
        1. @responses.activate (provided by the responses)
        2. @mock_api_response() (provided by test_utils.decorators)
        3. @mock_api_response_with_callback() (provided by test_utils.decorators)
        """
        responses.add(
            method=responses.POST,
            url=JwtEMSIApiClient.ACCESS_TOKEN_URL,
            json={'access_token': access_token, 'expires_in': expires_in}
        )
