"""
Management command for populating missing job names by extracting from EMSI.
"""

import logging

from edx_django_utils.db import chunked_queryset

from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError

from taxonomy.constants import get_lookup_query_filter
from taxonomy.emsi_client import EMSIJobsApiClient
from taxonomy.enums import RankingFacet
from taxonomy.exceptions import TaxonomyAPIError
from taxonomy.models import Job

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Command for populating missing job names.

    In refresh_job_skills command we are creating Jobs using external id only (without providing their names). This
    command will filter all the Jobs that do not have names in it and populate.

    Example usage:
        $ # Update the existing job names.
        $ ./manage.py populate_job_names
        """
    help = 'Populates missing Job names in the system.'

    def _update_job_names(self, job_bucket):
        """
        Persist the Jobs data in the database.
        """
        job_id = job_bucket['id']
        job_name = job_bucket['properties']['singular_name']
        try:
            Job.objects.update_or_create(external_id=job_id, defaults={'name': job_name})
        except IntegrityError:
            LOGGER.exception(
                f'Integrity error on attempt to create/update job with name {job_name}.'
            )

    def _update_jobs(self):
        """
        Fetch the Jobs with missing names from EMSI and update their names.
        """
        client = EMSIJobsApiClient()
        ranking_facet = RankingFacet.TITLE
        try:
            jobs = Job.objects.filter(name=None)
            for chunked_jobs in chunked_queryset(jobs):
                jobs_external_ids = list(chunked_jobs.values_list('external_id', flat=True))
                jobs = client.get_details(
                    ranking_facet=ranking_facet,
                    query_filter=get_lookup_query_filter(jobs_external_ids)
                )
                buckets = jobs['data']
                for bucket in buckets:
                    self._update_job_names(bucket)
        except TaxonomyAPIError as error:
            message = f'Taxonomy API Error for updating the jobs for Ranking Facet {ranking_facet} Error: {error}.'
            LOGGER.error(message)
            raise CommandError(message)
        except KeyError as error:
            message = f'Missing keys in update Job names. Error: {error}.'
            LOGGER.error(message)
            raise CommandError(message)

    def handle(self, *args, **options):
        """
        Entry point for management command execution.
        """
        LOGGER.info('Populate Job names process started.')
        self._update_jobs()
        LOGGER.info('Populate Job names process finished successfully.')
