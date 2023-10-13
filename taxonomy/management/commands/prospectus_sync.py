"""
Management command for syncing Courses and Subjects from Discovery to Contentful.
"""

import logging

from taxonomy.discovery.discovery_courses import get_courses_page
from taxonomy.contentful.contentful_courses import process_discovery_courses
from django.core.management.base import BaseCommand

LOGGER = logging.getLogger(__name__)

class Command(BaseCommand):
    """
    Management command for fetching and syncing Courses and Subjects from Discovery to Contentful.

    Example usage:
        $ # Sync Courses and Subjects from Discovery to Contentful
        $ ./manage.py prospectus_sync
        """
    help = 'Sync Courses and Subjects from Discovery to Contentful'

    async def process_discovery_course_url(url):
        if not url:
            return
        
        # next includes offset
        # https://discovery.edx.org/api/v1/courses/?limit=20&offset=20
        discovery_courses, next_page = await get_courses_page(url)
        if not discovery_courses or len(discovery_courses) == 0:
            return
        
        await process_discovery_courses(discovery_courses)

    def handle(self, *args, **options):
        """
        Runs the code to reindex algolia.
        """
        LOGGER.info('[TAXONOMY] Calling process_discovery_course_url.')
        self.process_discovery_course_url('https://discovery.edx.org/api/v1/courses/?limit=20&offset=20')
        LOGGER.info('[TAXONOMY] process_discovery_course_url from command prospectus_sync finished successfully.')
