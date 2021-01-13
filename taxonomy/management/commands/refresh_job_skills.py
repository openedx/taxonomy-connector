"""
Management command for refreshing the skills associated with courses.
"""

import logging

from django.core.management.base import BaseCommand, CommandError

from taxonomy.emsi_client import EMSIJobsApiClient
from taxonomy.enums import RankingFacet
from taxonomy.exceptions import TaxonomyAPIError
from taxonomy.models import Job, JobSkills, Skill

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Command to refresh the jobs associated with skills.

    Example usage:
        $ # Create or refresh the existing data associated with jobs and job skills.
        $ ./manage.py refresh_job_skills
        """
    help = 'Refreshes the jobs associated with skills.'

    def _update_jobs_data(self, job_skill_bucket):
        """
        Persist the jobs data in the database.
        """
        job, __ = Job.objects.update_or_create(name=job_skill_bucket['name'])
        jobs_bucket = job_skill_bucket['ranking']['buckets']
        for skill_data in jobs_bucket:
            skill, __ = Skill.objects.get_or_create(external_id=skill_data['name'])
            JobSkills.objects.update_or_create(
                job=job,
                skill=skill,
                defaults={
                    'significance': skill_data['significance'],
                    'unique_postings': skill_data['unique_postings'],
                },
            )

    def _refresh_jobs(self, ranking_facet, nested_ranking_facet):
        """
        Refreshes the jobs associated with the skills.

        Arguments:
            ranking_facet (RankingFacet): Data will be ranked by this facet.
            nested_ranking_facet (RankingFacet): This is the nested facet to be applied after ranking data by the
                `ranking_facet`.
        """
        client = EMSIJobsApiClient()
        try:
            jobs = client.get_jobs(
                ranking_facet,
                nested_ranking_facet,
            )
        except TaxonomyAPIError:
            message = 'Taxonomy API Error for refreshing the jobs for ' \
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
        """
        self._refresh_jobs(RankingFacet.TITLE_NAME, RankingFacet.SKILLS)
