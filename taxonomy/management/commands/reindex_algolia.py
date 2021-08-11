"""
Management command to index/reindex taxonomy data on algolia.
"""
import logging

from django.core.management.base import BaseCommand

from taxonomy.algolia.utils import index_jobs_data_in_algolia

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Management command to index/reindex taxonomy data on algolia.
    """
    help = (
        'Reindex taxonomy jobs data in Algolia.'
    )

    def handle(self, *args, **options):
        """
        Runs the code to reindex algolia.
        """
        LOGGER.info('[TAXONOMY] Calling index_jobs_data_in_algolia.')
        index_jobs_data_in_algolia()
        LOGGER.info('[TAXONOMY] index_jobs_data_in_algolia from command reindex_algolia finished successfully.')
