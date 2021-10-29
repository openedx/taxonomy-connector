# -*- coding: utf-8 -*-
"""
Utility functions related to algolia indexing.
"""
import logging

from django.conf import settings

from taxonomy.algolia.client import AlgoliaClient
from taxonomy.algolia.constants import ALGOLIA_JOBS_INDEX_SETTINGS, JOBS_PAGE_SIZE
from taxonomy.algolia.serializers import JobSerializer
from taxonomy.models import Job

LOGGER = logging.getLogger(__name__)


def index_jobs_data_in_algolia():
    """
    Re-Index all jobs data to algolia.

    This function is responsible for
        1. Constructing a list of dicts containing all jobs present in the database.
        2. Re-Indexing all data in a single atomic operations with zero downtime.

    Note: We need to construct a list of all jobs in the form of a list and the send it all in a single attempt to
        make the operation atomic and make sure there is no downtime. Paginating DB data and incrementally adding
        objects to the index will cause downtime equal to the amount of time it will take to run the command.
    """
    client = AlgoliaClient(
        application_id=settings.ALGOLIA.get('APPLICATION_ID'),
        api_key=settings.ALGOLIA.get('API_KEY'),
        index_name=settings.ALGOLIA.get('TAXONOMY_INDEX_NAME'),
    )
    LOGGER.info('[TAXONOMY] Resetting algolia index settings from code.')
    client.set_index_settings(ALGOLIA_JOBS_INDEX_SETTINGS)

    LOGGER.info('[TAXONOMY] Fetching Jobs data from the database.')
    jobs_data = fetch_jobs_data()
    LOGGER.info('[TAXONOMY] Jobs data successfully fetched from the database.')
    LOGGER.info('[TAXONOMY] Indexing Jobs data on algolia.')
    client.replace_all_objects(jobs_data)
    LOGGER.info('[TAXONOMY] Jobs data successfully indexed on algolia.')


def fetch_jobs_data():
    """
    Construct a list of all the jobs from the database.

    Returns:
        (list<dict>): A list of dicts containing job data.
    """
    start, page_size = 0, JOBS_PAGE_SIZE
    jobs = []

    qs = Job.objects.exclude(name__isnull=True)

    while qs[start:start + page_size].exists():
        job_serializer = JobSerializer(qs[start:start + page_size], many=True)
        jobs.extend(job_serializer.data)
        start += page_size

    return jobs
