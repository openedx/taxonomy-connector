"""
Management command for populating missing job names by extracting from EMSI.
"""

import logging

from django.core.management.base import BaseCommand, CommandError

from taxonomy.constants import get_lookup_query_filter
from taxonomy.emsi_client import EMSIJobsApiClient
from taxonomy.enums import RankingFacet
from taxonomy.exceptions import TaxonomyAPIError
from taxonomy.models import Job
from taxonomy.utils import chunked_queryset

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    command for populating missing job names

    While creating Job object we only populate its id. We need to get all the Job in the system that do no have names.

    Example usage:
        $ # Update the existing job names.
        $ ./manage.py populate_job_names
        """
    help = 'populating missing Job names in the system.'

    def _update_job(self, job_bucket):
        """
        Persist the jobs data in the database.
        """
        job_id = job_bucket['id']
        job_name = job_bucket['properties']['singular_name']
        Job.objects.update_or_create(external_id=job_id, defaults={'name': job_name})

    def _update_jobs(self):
        """
        Updated the Jobs by fetching data from EMSI
        """
        client = EMSIJobsApiClient()
        ranking_facet = RankingFacet.TITLE
        try:
            jobs = Job.objects.filter(name='')
            for chunked_jobs in chunked_queryset(jobs):
                jobs_external_ids = list(chunked_jobs.values_list('external_id', flat=True))
                jobs = client.get_details(
                    ranking_facet=ranking_facet,
                    query_filter=get_lookup_query_filter(jobs_external_ids)
                )
                buckets = jobs['data']
                for bucket in buckets:
                    self._update_job(bucket)
        except TaxonomyAPIError as error:
            message = 'Taxonomy API Error for updating the jobs for Ranking Facet {} Error: {}'.format(
                ranking_facet, error
            )
            LOGGER.error(message)
            raise CommandError(message)
        except KeyError as error:
            message = f'Missing keys in update Job names. Error: {error}'
            LOGGER.error(message)
            raise CommandError(message)

    def handle(self, *args, **options):
        """
        Entry point for management command execution.
        """
        self._update_jobs()
