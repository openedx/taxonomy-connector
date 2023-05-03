# -*- coding: utf-8 -*-
"""
Management command for generating job descriptions using chatGPT.
"""

import logging
from concurrent.futures import ThreadPoolExecutor

from django.core.management.base import BaseCommand

from taxonomy.models import Job
from taxonomy.utils import generate_and_store_job_description

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Command to generate job descriptions using chatGPT.

    Example usage:
        $ ./manage.py generate_job_descriptions
    """
    help = 'Command to generate job descriptions using chatGPT'

    def handle(self, *args, **options):
        """
        Entry point for management command execution.
        """
        LOGGER.info('Command started. Generating job descriptions for all jobs.')

        with ThreadPoolExecutor(max_workers=40) as executor:
            for job in Job.objects.exclude(name__isnull=True).filter(description=''):
                executor.submit(generate_and_store_job_description, job.external_id, job.name)

        LOGGER.info('Command completed. Successfully generated job descriptions for all jobs.')
