"""
Management command for refreshing the skills associated with courses.
"""

import logging

from django.core.management.base import BaseCommand, CommandError
from taxonomy.emsi_client import EMSIJobsApiClient
from taxonomy.enums import RankingFacet
from taxonomy.models import Job, JobSkills

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    """
        Example usage:
            $ ./manage.py refresh_skills_jobs
        """
    help = 'Refreshes the jobs associated with skills.'

    def _refresh_jobs(self):
        """
        Refreshes the jobs associated with the skills.
        """
        client = EMSIJobsApiClient()
        jobs = client.get_jobs(
            RankingFacet.TITLE_NAME,
            RankingFacet.SKILLS_NAME,
        )
        if jobs:
            buckets = jobs['data']['ranking']['buckets']
            for x in range(0, len(buckets)):
                try:
                    job_skill_bucket = buckets[x]
                    job, created = Job.objects.update_or_create(name=job_skill_bucket['name'])
                    jobs_bucket = job_skill_bucket['ranking']['buckets']
                    for y in range(0, len(jobs_bucket)):
                        skill_data = jobs_bucket[y]
                        jobs, created = JobSkills.objects.update_or_create(job=job,
                                                                               name=skill_data['name'],
                                                                               defaults={
                                                                                   'significance': skill_data['significance'],
                                                                                   'unique_postings': skill_data['unique_postings'],
                                                                               })
                except KeyError:
                    LOGGER.error('Missing keys in skills data for',)

    def handle(self, *args, **options):
        """
        Entry point for management command execution.
        """
        self._refresh_jobs()
