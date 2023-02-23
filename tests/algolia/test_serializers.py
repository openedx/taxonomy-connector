"""
Tests for algolia serializers.
"""
import mock
from pytest import mark

from taxonomy.algolia.serializers import JobSerializer
from taxonomy.models import Job
from test_utils import factories
from test_utils.testcase import TaxonomyTestCase


@mark.django_db
class TestJobSerializer(TaxonomyTestCase):
    """
    Validate serialization logic for algolia.
    """

    @mock.patch('taxonomy.algolia.utils.JOBS_PAGE_SIZE', 5)  # this is done to trigger the pagination flow.
    def test_jobs_data(self):
        """
        Test that serializer returns data for all fields and nested serializers.
        """
        # Add test data.
        job_skills = factories.JobSkillFactory.create_batch(15)
        for job_skill in job_skills:
            factories.JobPostingsFactory.create(job=job_skill.job)

        data = {
            'jobs_with_recommendations': [
                {
                    "name": "Job Name 1",
                    "similar_jobs": ["Job A", "Job B", "Job C"]
                },
                {
                    "name": "Job Name 2",
                    "similar_jobs": ["Job A", "Job B", "Job C"]
                },
            ]
        }
        job_serializer = JobSerializer(Job.objects, context=data, many=True)
        jobs_data = job_serializer.data

        # Assert all jobs are included in the data returned by the serializer
        assert len(jobs_data) == 15

        # Assert ID is present
        assert all('id' in job_data for job_data in jobs_data)

        # Assert Object ID is present
        assert all('objectID' in job_data for job_data in jobs_data)

        # Assert skills is present and has correct data
        assert all('skills' in job_data for job_data in jobs_data)
        assert all('name' in job_data['skills'][0] for job_data in jobs_data)

        # Assert job_postings is present and has correct data
        assert all('job_postings' in job_data for job_data in jobs_data)
        assert all('median_salary' in job_data['job_postings'][0] for job_data in jobs_data)
        assert all('job_id' in job_data['job_postings'][0] for job_data in jobs_data)

        # Assert similar_jobs is present and has correct data
        assert all('similar_jobs' in job_data for job_data in jobs_data)

        # Assert industries is present and has correct data
        assert all('industries' in job_data for job_data in jobs_data)
