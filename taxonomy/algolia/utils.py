# -*- coding: utf-8 -*-
"""
Utility functions related to algolia indexing.
"""
import logging
from collections import deque, namedtuple
from datetime import datetime

from django.conf import settings
from django.db.models import Q, Sum

from taxonomy.algolia.client import AlgoliaClient
from taxonomy.algolia.constants import (
    ALGOLIA_JOBS_INDEX_SETTINGS,
    EMBEDDED_OBJECT_LENGTH_CAP,
    JOBS_PAGE_SIZE,
    JOBS_TO_IGNORE,
)
from taxonomy.algolia.serializers import JobSerializer
from taxonomy.models import Industry, IndustryJobSkill, Job, JobSkills

LOGGER = logging.getLogger(__name__)

JobRecommendation = namedtuple('JobRecommendation', 'name similarity')


class LogTime:
    """
    Context manager to calculate and log the time taken by a piece of code.
    """
    start = None

    def __init__(self, message_prefix):
        """
        Initialize the context with the message prefix.
        """
        self.message_prefix = message_prefix

    def __enter__(self):
        """
        Start tracking the time.
        """
        self.start = datetime.now()

    def __exit__(self, *args, **kwargs):
        """
        End time tracking and log the time taken by a piece of code.
        """
        end = datetime.now()
        LOGGER.info('%s: %s', self.message_prefix, end - self.start)


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


def calculate_jaccard_similarity(set_a, set_b):
    """
    Calculate Jaccard similarity between two sets of job skills.
    """
    try:
        return len(set_a.intersection(set_b)) / len(set_a.union(set_b))
    except ZeroDivisionError:
        return float(0)


def calculate_job_skills(jobs_qs):
    """
    Fetch and skills for each job.

    Arguments:
        jobs_qs (QuerySet): Django queryset of Job model that will be used as a starting point to fetch skills data.

    Returns:
        (dict<str: dict>): A dictionary with job name as the key and the value against each key is a dict containing
            job details, including `skills`.
    """
    job_details = {}
    for job in jobs_qs.all():
        skills = set(
            JobSkills.get_whitelisted_job_skill_qs().filter(job=job).values_list('skill__name', flat=True)
        )
        job_details[job.name] = {
            'skills': skills,
        }

    return job_details


def calculate_job_recommendations(jobs_data):
    """
    Calculate job recommendations.

    Note: `jobs_data` will be treated as mutable (instead of creating a new dict to return)
        to reduce memory footprint of this function.

    Arguments:
        jobs_data (dict<str: dict>): A dictionary containing jobs data like skills. key of the dict is jobs name and
            the value dict should at-least contain a set of skills against `skills` key.

    Returns:
        (dict<str: dict>): The same dict from the argument, with `similar_jobs` added against each job.
    """
    SIMILAR_JOBS_COUNT = 3
    for job_name, job in jobs_data.items():
        job_recommendations = deque([], maxlen=SIMILAR_JOBS_COUNT)
        for candidate_job_name, candidate_job in jobs_data.items():
            if job_name == candidate_job_name:
                continue

            jaccard_similarity = calculate_jaccard_similarity(job['skills'], candidate_job['skills'])

            insert_item_in_ordered_queue(
                queue=job_recommendations,
                item=JobRecommendation(candidate_job_name, jaccard_similarity),
                key=lambda item: item.similarity,
            )

        jobs_data[job_name]['similar_jobs'] = [item.name for item in job_recommendations]

    return jobs_data


def fetch_and_combine_job_details(jobs_qs):
    """
    Fetch data related to jobs, combine it in the form of a dict and return.

    The jobs data that we are interested in is listed below.
    1. skills: A set of skills that are associated with the corresponding job.
    2. similar_jobs: Other jobs that are similar to the corresponding job.

    Arguments:
        jobs_qs (QuerySet): Django queryset of Job model that will be used as a starting point to fetch skills data.

    Returns:
        (dict<str: dict>): A dictionary with job name as the key and the value against each key is a dict containing
            job details, including `skills` and `similar_jobs`.
    """
    with LogTime('[TAXONOMY] Time taken to fetch and combine skills data for jobs'):
        jobs_data = calculate_job_skills(jobs_qs)

    with LogTime('[TAXONOMY] Time taken to fetch and combine job recommendations'):
        jobs_data = calculate_job_recommendations(jobs_data=jobs_data)

    return jobs_data


def insert_item_in_ordered_queue(queue, item, key=lambda arg: arg):
    """
    Insert given job in the jobs list.

    `queue` is assumed to be ordered based on given key in the descending order.
    `item` is the item to insert in the list, it will be inserted in the correct place.

    Note: item will not be inserted if there is no place for it based on the key.

    Arguments:
        queue (deque<Any>): A Queue containing list of items.
        item (Any): Item that needs to be inserted.
        key (func): Optional key to get the comparable attribute of the item.
    """
    for index, element in enumerate(queue):
        if key(item) > key(element):
            if len(queue) == queue.maxlen:
                # remove the last element of the queue to avoid index error.
                queue.pop()
            queue.insert(index, item)

            # Item is inserted, return here.
            return

    # If item could not be inserted, then check for available space, and insert the item if there is space.
    if len(queue) != queue.maxlen:
        queue.append(item)
        return


def combine_industry_skills():
    """
    Constructs a dict with keys as industry names and values as their skills.
    """
    industries_and_skills = {}
    for industry in Industry.objects.all():
        # sum all significances for the same skill and then sort on total significance
        skills = list(
            IndustryJobSkill.get_whitelisted_job_skill_qs().filter(
                industry=industry
            ).values_list(
                'skill__name', flat=True
            ).annotate(
                total_significance=Sum('significance')
            ).order_by(
                '-total_significance'
            ).distinct()[:EMBEDDED_OBJECT_LENGTH_CAP]
        )
        industries_and_skills[industry.name] = skills
    return industries_and_skills


def get_job_ids(qs):
    """
     Get a set of all the job id.
    """
    batch_size = 20000
    jobs = set()

    offset, limit = 0, batch_size
    qs = qs.all()
    while qs[offset:offset + limit].exists():
        jobs = jobs.union(qs[offset:offset + limit].values_list('job_id', flat=True))
        offset = offset + limit
    return jobs


def fetch_jobs_data():
    """
    Construct a list of all the jobs from the database.

    Returns:
        (list<dict>): A list of dicts containing job data.
    """
    qs = Job.objects.exclude(Q(name__isnull=True) | Q(external_id__in=JOBS_TO_IGNORE))

    LOGGER.info('[TAXONOMY] Started combining skills and recommendations data for the jobs.')
    jobs_data = fetch_and_combine_job_details(qs)
    LOGGER.info('[TAXONOMY] Finished calculating job recommendations and skills.')

    with LogTime('[TAXONOMY] Time taken to combine industry skills data'):
        industry_skills = combine_industry_skills()

    start, page_size = 0, JOBS_PAGE_SIZE
    jobs = []
    LOGGER.info(f'[TAXONOMY] Started serializing Jobs data. Total Jobs: {qs.count()}')
    while qs[start:start + page_size].exists():
        job_serializer = JobSerializer(
            qs[start:start + page_size],
            many=True,
            context={
                'jobs_data': jobs_data,
                'industry_skills': industry_skills,
                'jobs_having_job_skills': get_job_ids(JobSkills.get_whitelisted_job_skill_qs()),
                'jobs_having_industry_skills': get_job_ids(IndustryJobSkill.get_whitelisted_job_skill_qs()),
            },
        )
        jobs.extend(job_serializer.data)
        start += page_size

    return jobs
