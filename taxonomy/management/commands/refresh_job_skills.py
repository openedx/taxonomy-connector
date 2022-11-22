"""
Management command for refreshing the skills associated with courses.
"""

import logging

from edx_django_utils.db import chunked_queryset

from django.core.management.base import BaseCommand, CommandError

from taxonomy.constants import get_job_query_filter
from taxonomy.emsi.client import EMSIJobsApiClient
from taxonomy.enums import RankingFacet
from taxonomy.exceptions import TaxonomyAPIError
from taxonomy.models import Job, JobSkills, Skill, IndustryJobSkill, Industry

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Command to refresh the jobs associated with skills.

    Example usage:
        $ # Create or refresh the existing data associated with jobs and job skills.
        $ ./manage.py refresh_job_skills
        """
    help = 'Refreshes the jobs associated with skills.'

    @staticmethod
    def _update_job_skills(job_bucket, industry=None):
        """
        Persist the jobs data in the database.
        """
        job_id = job_bucket['name']
        job, _ = Job.objects.get_or_create(external_id=job_id)
        skill_buckets = job_bucket['ranking']['buckets']
        for skill_bucket in skill_buckets:
            skill_id = skill_bucket['name']
            try:
                skill = Skill.objects.get(external_id=skill_id)
            except Skill.DoesNotExist:
                LOGGER.warning('Skill %s not found', skill_id)
                continue

            relation_model = JobSkills
            relation_kwargs = {
                'job': job,
                'skill': skill,
                'defaults': {
                    'significance': skill_bucket['significance'],
                    'unique_postings': skill_bucket['unique_postings'],
                },
            }
            if industry:
                relation_model = IndustryJobSkill
                relation_kwargs['industry'] = industry
            relation_model.objects.update_or_create(**relation_kwargs)

    def _refresh_job_skills(self, ranking_facet, nested_ranking_facet):
        """
        Refreshes the jobs associated with the skills.

        Arguments:
            ranking_facet (RankingFacet): Data will be ranked by this facet.
            nested_ranking_facet (RankingFacet): This is the nested facet to be applied after ranking data by the
                `ranking_facet`.
        """
        client = EMSIJobsApiClient()
        try:
            skills = Skill.objects.all()
            for chunked_skills in chunked_queryset(skills, chunk_size=50):
                skill_external_ids = list(chunked_skills.values_list('external_id', flat=True))
                jobs = client.get_jobs(
                    ranking_facet=ranking_facet,
                    nested_ranking_facet=nested_ranking_facet,
                    query_filter=get_job_query_filter(skill_external_ids)
                )
                job_buckets = jobs['data']['ranking']['buckets']
                for bucket in job_buckets:
                    self._update_job_skills(bucket)

                for industry in Industry.objects.all():
                    jobs = client.get_jobs(
                        ranking_facet=ranking_facet,
                        nested_ranking_facet=nested_ranking_facet,
                        query_filter=get_job_query_filter(skill_external_ids, industry)
                    )
                    job_buckets = jobs['data']['ranking']['buckets']
                    for bucket in job_buckets:
                        self._update_job_skills(bucket, industry)

        except TaxonomyAPIError as error:
            message = 'Taxonomy API Error for refreshing the jobs for Ranking Facet {} and Nested Ranking Facet {}, ' \
                      'Error: {}'.format(ranking_facet, nested_ranking_facet, error)
            LOGGER.error(message)
            raise CommandError(message)
        except KeyError as error:
            message = f'Missing keys in update job skills data. Error: {error}'
            LOGGER.error(message)
            raise CommandError(message)

    def handle(self, *args, **options):
        """
        Entry point for management command execution.
        """
        self._refresh_job_skills(RankingFacet.TITLE, RankingFacet.SKILLS)
