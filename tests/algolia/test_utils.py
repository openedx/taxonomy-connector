"""
Tests for algolia utility functions.
"""
import mock
from pytest import mark

from taxonomy.algolia.constants import ALGOLIA_JOBS_INDEX_SETTINGS
from taxonomy.algolia.utils import calculate_jaccard_similarity, fetch_jobs_data, index_jobs_data_in_algolia
from test_utils import factories
from test_utils.testcase import TaxonomyTestCase


@mark.django_db
class TestUtils(TaxonomyTestCase):
    """
    Validate algolia utility functions.
    """

    def test_calculate_jaccard_similarity(self):
        """
        Test that calculate_jaccard_similarity returns correct value.
        """
        # Test an edge case where skills cam be two empty sets
        set_a = set([])
        set_b = set([])
        assert calculate_jaccard_similarity(set_a, set_b) == 0

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
        assert all('industries' in job_data for job_data in jobs_data)
        assert all('similar_jobs' in job_data for job_data in jobs_data)

    @mock.patch('taxonomy.algolia.utils.JOBS_PAGE_SIZE', 5)
    def test_fetch_industry_job_skill_data(self):
        """
        Test test_fetch_industry_job_skill_data returns data for available jobs with unique industry names
        """
        industry_1 = factories.IndustryFactory(code=12, name='mining')
        skill_1 = factories.SkillFactory(external_id='SKILL-1', name='skill_1')
        skill_2 = factories.SkillFactory(external_id='SKILL-2', name='skill_2')
        job_1 = factories.JobFactory(
            external_id='JOB-test1',
            name='test1'
        )
        factories.IndustryJobSkillFactory(
            industry=industry_1,
            skill=skill_1,
            job=job_1,
            significance=1,
            unique_postings=12121)
        factories.IndustryJobSkillFactory(
            industry=industry_1,
            skill=skill_2,
            job=job_1,
            significance=2,
            unique_postings=12131
        )

        jobs_data = fetch_jobs_data()

        # Assert industrie_names are unique
        assert all(len(set(job_data['industry_names'])) == len(job_data['industry_names']) for job_data in jobs_data)

    @mock.patch('taxonomy.algolia.utils.JOBS_PAGE_SIZE', 5)
    @mock.patch('taxonomy.algolia.utils.EMBEDDED_OBJECT_LENGTH_CAP', 2)
    def test_fetch_industry_skills_data(self):
        """
        Test that fetch_jobs_data returns industries along with top 2 skills with highest significance
        for the available jobs.
        """
        industry_1 = factories.IndustryFactory(code=12, name='mining')
        skill_1 = factories.SkillFactory(external_id='SKILL-1', name='skill_1')
        skill_2 = factories.SkillFactory(external_id='SKILL-2', name='skill_2')
        # third skill with lowset significance
        skill_3 = factories.SkillFactory(external_id='SKILL-3', name='skill_3')

        job_1 = factories.JobFactory(
            external_id='JOB-test1',
            name='test1'
        )
        factories.IndustryJobSkillFactory(
            industry=industry_1,
            skill=skill_1,
            job=job_1,
            significance=3,
            unique_postings=12121)
        factories.IndustryJobSkillFactory(
            industry=industry_1,
            skill=skill_2,
            job=job_1,
            significance=2,
            unique_postings=12131
        )
        factories.IndustryJobSkillFactory(
            industry=industry_1,
            skill=skill_3,
            job=job_1,
            significance=1,
            unique_postings=12133
        )

        jobs_data = fetch_jobs_data()
        assert jobs_data[0]['industries'] == [
            {
                'name': industry_1.name,
                'skills': [skill_1.name, skill_2.name],
            }
        ]

    @mock.patch('taxonomy.algolia.utils.JOBS_PAGE_SIZE', 5)
    @mock.patch('taxonomy.algolia.utils.EMBEDDED_OBJECT_LENGTH_CAP', 2)
    def test_fetch_industry_skills_data_with_duplicate_skills(self):
        """
        Test that fetch_jobs_data returns industries along with top 2 skills with the highest sum of significance
        values for duplicate skills.
        """
        industry_1 = factories.IndustryFactory(code=12, name='mining')
        skill_1 = factories.SkillFactory(external_id='SKILL-1', name='skill_1')
        skill_2 = factories.SkillFactory(external_id='SKILL-2', name='skill_2')
        skill_3 = factories.SkillFactory(external_id='SKILL-3', name='skill_3')

        job_1 = factories.JobFactory(
            external_id='JOB-test1',
            name='test1'
        )
        job_2 = factories.JobFactory(
            external_id='JOB-test2',
            name='test2'
        )
        factories.IndustryJobSkillFactory(
            industry=industry_1,
            skill=skill_1,
            job=job_1,
            significance=2,
            unique_postings=12121)
        factories.IndustryJobSkillFactory(
            industry=industry_1,
            skill=skill_1,
            job=job_2,
            significance=2,
            unique_postings=12131
        )
        factories.IndustryJobSkillFactory(
            industry=industry_1,
            skill=skill_2,
            job=job_1,
            significance=3,
            unique_postings=12133
        )
        factories.IndustryJobSkillFactory(
            industry=industry_1,
            skill=skill_3,
            job=job_1,
            significance=2,
            unique_postings=12133
        )

        jobs_data = fetch_jobs_data()
        assert jobs_data[0]['industries'] == [
            {
                'name': industry_1.name,
                'skills': [skill_1.name, skill_2.name],
            }
        ]

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
