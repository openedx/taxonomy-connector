"""
Tests for algolia utility functions.
"""
import mock
from pytest import mark

from taxonomy.algolia.constants import ALGOLIA_JOBS_INDEX_SETTINGS
from taxonomy.algolia.utils import fetch_jobs_data, index_jobs_data_in_algolia
from test_utils import factories
from test_utils.testcase import TaxonomyTestCase


@mark.django_db
class TestUtils(TaxonomyTestCase):
    """
    Validate algolia utility functions.
    """

    @mock.patch('taxonomy.algolia.utils.JOBS_PAGE_SIZE', 5)  # this is done to trigger the pagination flow.
    def test_fetch_jobs_data(self):
        """
        Test that fetch_jobs_data returns data for available jobs.
        """
        # Add test data.
        job_skills = factories.JobSkillFactory.create_batch(15)
        for job_skill in job_skills:
            factories.JobPostingsFactory.create(job=job_skill.job)

        jobs_data = fetch_jobs_data()

        # Assert all jobs are included in the data returned by the serializer
        assert len(jobs_data) == 15

        # Assert Object ID is present
        assert all('objectID' in job_data for job_data in jobs_data)

        # Assert skills is present and has correct data
        assert all('skills' in job_data for job_data in jobs_data)
        assert all('name' in job_data['skills'][0] for job_data in jobs_data)

        # Assert job_postings is present and has correct data
        assert all('job_postings' in job_data for job_data in jobs_data)
        assert all('median_salary' in job_data['job_postings'][0] for job_data in jobs_data)
        assert all('job_id' in job_data['job_postings'][0] for job_data in jobs_data)

        assert all('industry_names' in job_data for job_data in jobs_data)

    @mock.patch('taxonomy.algolia.utils.JOBS_PAGE_SIZE', 5)  # this is done to trigger the pagination flow.
    @mock.patch('taxonomy.algolia.client.algoliasearch.Client')
    def test_index_jobs_data_in_algolia(self, algolia_search_client_mock):
        """
        Test index_jobs_data_in_algolia works as expected.
        """
        # Setup mocking
        set_settings_mock = mock.MagicMock()
        replace_all_objects_mock = mock.MagicMock()
        index_mock = mock.MagicMock(set_settings=set_settings_mock, replace_all_objects=replace_all_objects_mock)
        algolia_search_client_mock.return_value.init_index.return_value = index_mock

        # Add test data.
        job_skills = factories.JobSkillFactory.create_batch(15)
        for job_skill in job_skills:
            factories.JobPostingsFactory.create(job=job_skill.job)

        # Call the index function.
        index_jobs_data_in_algolia()

        set_settings_mock.assert_called_once_with(ALGOLIA_JOBS_INDEX_SETTINGS)
        replace_all_objects_mock.assert_called_once_with(mock.ANY, mock.ANY)
