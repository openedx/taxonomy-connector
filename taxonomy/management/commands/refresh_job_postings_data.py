"""
Management command for refreshing the skills associated with courses.
"""

import logging

from edx_django_utils.db import chunked_queryset

from django.core.management.base import BaseCommand, CommandError

from taxonomy.constants import get_job_posting_query_filter
from taxonomy.emsi_client import EMSIJobsApiClient
from taxonomy.enums import RankingFacet
from taxonomy.exceptions import TaxonomyAPIError
from taxonomy.models import Job, JobPostings

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Command to refresh the job postings data associated with a job.

    Example usage:
        $ # Create or refresh the existing data associated with jobs and job postings on the basis
        $ # of ranking_facet TITLE(which returns id of the job)
        $ ./manage.py refresh_job_postings_data
    """
    help = 'Refreshes the job postings data associated with a job.'

    def _update_job_postings_data(self, job_external_id, job_posting_bucket):
        """
        Persist the jobs postings data in the database.

        Arguments:
            job_external_id (str): id of the job to save.
            job_posting_bucket (dict): A dictionary containing field values for JobPosting model.
        """
        try:
            job = Job.objects.get(external_id=job_external_id)
            JobPostings.objects.update_or_create(job=job, defaults=job_posting_bucket)
        except Job.DoesNotExist:
            LOGGER.warning('Unable to create JobPosting as no job with external_id %s exists.', job_external_id)

    def _refresh_job_postings(self, ranking_facet):
        """
        Refreshes the job postings data associated with the jobs.

        Arguments:
            ranking_facet (RankingFacet): Data will be ranked by this facet.
        """
        client = EMSIJobsApiClient()
        try:
            jobs = Job.objects.all()
            for chunked_jobs in chunked_queryset(jobs):
                job_external_ids = list(chunked_jobs.values_list('external_id', flat=True))
                job_postings_data = client.get_job_postings(
                    ranking_facet=ranking_facet,
                    query_filter=get_job_posting_query_filter(job_external_ids)
                )
                buckets = job_postings_data['data']['ranking']['buckets']
                for bucket in buckets:
                    try:
                        job_external_id = bucket['name']
                        job_posting_bucket_data = {
                            'median_salary': str(bucket['median_salary']).strip('$'),
                            'median_posting_duration': bucket['median_posting_duration'],
                            'unique_postings': bucket['unique_postings'],
                            'unique_companies': bucket['unique_companies'],
                        }
                        self._update_job_postings_data(job_external_id, job_posting_bucket_data)
                    except KeyError as error:
                        message = f'Missing keys in job postings data. Error: {error}'
                        LOGGER.error(message)
                        raise CommandError(message)

        except TaxonomyAPIError:
            message = 'Taxonomy API Error for refreshing the job postings data for ' \
                      'Ranking Facet {}'.format(ranking_facet)
            LOGGER.error(message)
            raise CommandError(message)

    def handle(self, *args, **options):
        """
        Entry point for management command execution.
        """
        self._refresh_job_postings(RankingFacet.TITLE)
