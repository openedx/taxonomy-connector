"""
Tests for algolia client.
"""
import mock

from django.conf import settings

from taxonomy.algolia.client import AlgoliaClient
from taxonomy.algolia.constants import ALGOLIA_JOBS_INDEX_SETTINGS
from test_utils.testcase import TaxonomyTestCase


class TestAlgoliaClient(TaxonomyTestCase):
    """
    Validate algolia client.
    """

    @mock.patch('taxonomy.algolia.client.algoliasearch.Client')
    def test_client(self, _):
        """
        Test that algolia client works as expected.
        """
        set_settings_mock = mock.MagicMock()
        replace_all_objects_mock = mock.MagicMock()

        jobs_data = [{'objectID': 'test-1', 'skills': ['skill-1', 'skill-2']}]

        client = AlgoliaClient(
            application_id=settings.ALGOLIA.get('APPLICATION_ID'),
            api_key=settings.ALGOLIA.get('API_KEY'),
            index_name=settings.ALGOLIA.get('TAXONOMY_INDEX_NAME'),
        )
        client.algolia_index = mock.MagicMock(
            set_settings=set_settings_mock, replace_all_objects=replace_all_objects_mock,
        )

        client.set_index_settings(ALGOLIA_JOBS_INDEX_SETTINGS)
        client.replace_all_objects(jobs_data)

        client.algolia_index.set_settings.assert_called_once_with(ALGOLIA_JOBS_INDEX_SETTINGS)
        client.algolia_index.replace_all_objects.assert_called_once_with(jobs_data, mock.ANY)
