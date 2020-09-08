"""
Management command for refreshing the skills associated with courses.
"""

import logging

from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import gettext as _
from taxonomy.emsi_client import EMSIJobsApiClient
from taxonomy.enums import RankingFacet
from taxonomy.models import Job, JobPostings
from taxonomy.exceptions import TaxonomyServiceAPIError

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    """
        Example usage:
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
            default='',
        )

    def _update_jobs_postings_data(self, job_posting_bucket):
        """
        Persist the jobs postings data
        """
        job, created = Job.objects.update_or_create(name=job_posting_bucket['name'])
        JobPostings.objects.update_or_create(
            job=job,
            median_salary=job_posting_bucket['median_salary'],
            median_posting_duration=job_posting_bucket['median_posting_duration'],
            unique_postings=job_posting_bucket['unique_postings'],
            unique_companies=job_posting_bucket['unique_companies']
        )

    def _refresh_job_postings(self, ranking_facet):
        """
        Refreshes the job postings data associated with the jobs.
        """
        failures = False
        client = EMSIJobsApiClient()
        try:
            job_postings_data = client.get_job_postings(RankingFacet[ranking_facet])
        except TaxonomyServiceAPIError:
            failures = True
            LOGGER.error('Taxonomy Service Error for refreshing the job postings data for '
                         'Ranking Facet {}'.format(ranking_facet))
        if job_postings_data:
            buckets = job_postings_data['data']['ranking']['buckets']
            for x in range(0, len(buckets)):
                try:
                    self._update_jobs_postings_data(buckets[x])
                except KeyError:
                    failures = True
                    LOGGER.error('Bucket job postings exception for Ranking Facet: {},'.format(ranking_facet))
        if failures:
            raise CommandError(
                _(
                    'Could not refresh job postings of the jobs for the following Ranking Facet: {}'
                ).format(ranking_facet)
            )

    def handle(self, *args, **options):
        """
        Entry point for management command execution.
        Args:
            ranking_facet (RankingFacet): Data will be ranked by this facet.
        """
        ranking_facet = options['ranking_facet']
        self._refresh_job_postings(ranking_facet)
