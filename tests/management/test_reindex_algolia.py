"""
Tests for reindex_algolia management command.
"""
import mock
from pytest import mark

from django.core.management import call_command

from taxonomy.algolia.constants import ALGOLIA_JOBS_INDEX_SETTINGS
from test_utils import factories
from test_utils.testcase import TaxonomyTestCase


@mark.django_db
class TestReIndexAlgolia(TaxonomyTestCase):
    """
    Validate reindex_algolia management command works correctly.
    """
    command = 'reindex_algolia'

    @mock.patch('taxonomy.algolia.client.algoliasearch.Client')
    def test_command(self, algolia_search_client_mock):
        """
        Test reindex_algolia management command works correctly.
        """
        # Setup mocking
        set_settings_mock = mock.MagicMock()
        replace_all_objects_mock = mock.MagicMock()
        index_mock = mock.MagicMock(set_settings=set_settings_mock, replace_all_objects=replace_all_objects_mock)
        algolia_search_client_mock.return_value.init_index.return_value = index_mock

        # Add test data.
        job_skills = factories.JobSkillFactory.create_batch(200)
        for job_skill in job_skills:
            factories.JobPostingsFactory.create(job=job_skill.job)

        call_command(self.command)

        set_settings_mock.assert_called_once_with(ALGOLIA_JOBS_INDEX_SETTINGS)
        replace_all_objects_mock.assert_called_once_with(mock.ANY, mock.ANY)
