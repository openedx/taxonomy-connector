"""
Management command for refreshing the skills associated with courses.
"""

import logging

from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import gettext as _
from taxonomy.emsi_client import EMSIJobsApiClient
from taxonomy.enums import RankingFacet
from taxonomy.models import Job, JobSkills
from taxonomy.exceptions import TaxonomyServiceAPIError

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    """
        Example usage:
        Create or refresh the existing data associated with jobs and job skills on the basis
        of ranking_facet and nested_ranking_facet arguments.
        $ ./manage.py refresh_job_skills 'CERTIFICATIONS' 'CERTIFICATIONS_NAME'
        """
    help = 'Refreshes the jobs associated with skills.'

    def add_arguments(self, parser):
        """
        Add arguments to the command parser.
        """
        parser.add_argument(
            'ranking_facet',
            action='store',
            help=_('Ranking Facet'),
        )

        parser.add_argument(
            'nested_ranking_facet',
            action='store',
            help=_('Nested Ranking Facet'),
        )

    def _update_jobs_data(self, job_skill_bucket):
        """
        Persist the jobs data
        """
        job, created = Job.objects.update_or_create(name=job_skill_bucket['name'])
        jobs_bucket = job_skill_bucket['ranking']['buckets']
        for skill_data in jobs_bucket:
            JobSkills.objects.update_or_create(job=job,
                                               name=skill_data['name'],
                                               defaults={
                                                   'significance': skill_data['significance'],
                                                   'unique_postings': skill_data['unique_postings'],
                                               })

    def _refresh_jobs(self, ranking_facet, nested_ranking_facet):
        """
        Refreshes the jobs associated with the skills.
        """
        client = EMSIJobsApiClient()
        try:
            jobs = client.get_jobs(
                RankingFacet[ranking_facet],
                RankingFacet[nested_ranking_facet],
            )
        except TaxonomyServiceAPIError:
            message = 'Taxonomy Service Error for refreshing the jobs for ' \
                      'Ranking Facet {} and Nested Ranking Facet {}'.format(ranking_facet, nested_ranking_facet)
            LOGGER.error(message)
            raise CommandError(message)
        else:
            buckets = jobs['data']['ranking']['buckets']
            for bucket in buckets:
                try:
                    self._update_jobs_data(bucket)
                except KeyError:
                    message = 'Bucket jobs exception for Ranking Facet {},' \
                              'Nested Ranking Facet {}.'.format(ranking_facet, nested_ranking_facet)
                    LOGGER.error(message)
                    raise CommandError(message)

    def handle(self, *args, **options):
        """
        Entry point for management command execution.
        Args:
            ranking_facet (RankingFacet): Data will be ranked by this facet.
            nested_ranking_facet (RankingFacet): This is the nested facet to be applied after ranking data by the
                `ranking_facet`.
        """
        ranking_facet, nested_ranking_facet = options['ranking_facet'], options['nested_ranking_facet']
        if not ranking_facet and nested_ranking_facet:
            raise CommandError(_('Error: the following arguments are required: ranking_facet, nested_ranking_facet'))

        self._refresh_jobs(ranking_facet, nested_ranking_facet)
