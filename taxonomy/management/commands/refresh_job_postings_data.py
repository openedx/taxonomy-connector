"""
Management command for refreshing the skills associated with courses.
"""

import logging

from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import gettext as _

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
        $ # of ranking_facet. In the following example, 'TITLE_NAME' could be any job title
        $ # e.g. 'Senior Software Engineer'
        $ ./manage.py refresh_job_postings_data 'TITLE_NAME'
    """
    help = 'Refreshes the job postings data associated with a job.'

    def add_arguments(self, parser):
        """
        Add arguments to the command parser.
        """
        parser.add_argument(
            'ranking_facet',
            action='store',
            help=_('Ranking Facet'),
        )

    def _update_job_postings_data(self, job_name, job_posting_bucket):
        """
        Persist the jobs postings data in the database.

        Arguments:
            job_name (str): Name of the job to save.
            job_posting_bucket (dict): A dictionary containing field values for JobPosting model.
        """
        job, __ = Job.objects.update_or_create(name=job_name)
        JobPostings.objects.update_or_create(job=job, **job_posting_bucket)

    def _refresh_job_postings(self, ranking_facet):
        """
        Refreshes the job postings data associated with the jobs.

        Arguments:
            ranking_facet (RankingFacet): Data will be ranked by this facet.
        """
        client = EMSIJobsApiClient()
        try:
            job_postings_data = client.get_job_postings(RankingFacet[ranking_facet])
        except TaxonomyAPIError:
            message = 'Taxonomy API Error for refreshing the job postings data for ' \
                      'Ranking Facet {}'.format(ranking_facet)
            LOGGER.error(message)
            raise CommandError(message)
        else:
            buckets = job_postings_data['data']['ranking']['buckets']
            for bucket in buckets:
                try:
                    job_name = bucket['name']
                    job_posting_bucket_data = {
                        'median_salary': str(bucket['median_salary']).strip('$'),
                        'median_posting_duration': bucket['median_posting_duration'],
                        'unique_postings': bucket['unique_postings'],
                        'unique_companies': bucket['unique_companies'],
                    }
                except KeyError:
                    message = 'Missing keys in job postings data'
                    LOGGER.error(message)
                    raise CommandError(message)
                else:
                    self._update_job_postings_data(job_name, job_posting_bucket_data)

    def handle(self, *args, **options):
        """
        Entry point for management command execution.
        """
        ranking_facet = options['ranking_facet']
        self._refresh_job_postings(ranking_facet)
