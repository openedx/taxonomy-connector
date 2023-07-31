# -*- coding: utf-8 -*-
"""
Utility functions related to algolia indexing.
"""
import logging
import datetime
from collections import deque, namedtuple

from django.conf import settings
from django.db.models import Sum

from taxonomy.algolia.client import AlgoliaClient
from taxonomy.algolia.constants import ALGOLIA_JOBS_INDEX_SETTINGS, JOBS_PAGE_SIZE, EMBEDDED_OBJECT_LENGTH_CAP
from taxonomy.algolia.serializers import JobSerializer
from taxonomy.models import Job, Industry, JobSkills, IndustryJobSkill

LOGGER = logging.getLogger(__name__)

JobRecommendation = namedtuple('JobRecommendation', 'name similarity')


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


def combine_jobs_and_skills_data(jobs_qs):
    """
    Combine jobs and skills data.

    Arguments:
        jobs_qs (QuerySet): Django queryset of Job model that will be used as a starting point to fetch skills data.

    Returns:
        (list<dict>): A list of dicts containing job and their skills in a list.
    """
    all_job_and_skills_data = []
    for job in jobs_qs.all():
        skills = list(
            JobSkills.objects.filter(job=job).values_list('skill__name', flat=True)
        )
        all_job_and_skills_data.append({
            'name': job.name,
            'skills': skills,
        })

    return all_job_and_skills_data


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


def calculate_job_recommendations(jobs):
    """
    Calculate job recommendations.

    Args:
        jobs (list<dict>): A list of dicts containing job and their skills in a list.

    Returns:
        (list<dict>): A list of dicts containing jobs and their recommended jobs.
    """
    SIMILAR_JOBS_COUNT = 3
    job_recommendations = deque([], maxlen=SIMILAR_JOBS_COUNT)
    jobs_and_recommendations = []

    # converting skills list into set, to avoid repeated converting in the nested loop.
    jobs = [
        {'name': job['name'], 'skills': set(job['skills'])} for job in jobs
    ]

    for job in jobs:
        for candidate_job in jobs:
            if job['name'] == candidate_job['name']:
                continue

            jaccard_similarity = calculate_jaccard_similarity(job['skills'], candidate_job['skills'])

            insert_item_in_ordered_queue(
                queue=job_recommendations,
                item=JobRecommendation(job['name'], jaccard_similarity),
                key=lambda item: item.similarity,
            )

        jobs_and_recommendations.append({
            'name': job['name'],
            'similar_jobs': [item.name for item in job_recommendations],
        })

    return jobs_and_recommendations


def combine_industry_skills():
    """
    Constructs a dict with keys as industry names and values as their skills.
    """
    industries_and_skills = {}
    for industry in Industry.objects.all():
        # sum all significances for the same skill and then sort on total significance
        skills = list(
            IndustryJobSkill.objects.filter(
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
    qs = Job.objects.exclude(name__isnull=True)

    combine_start_time = datetime.datetime.now()
    LOGGER.info('[TAXONOMY] Started combining Jobs and their skills for recommendations calculation.')
    all_job_and_skills = combine_jobs_and_skills_data(qs)
    industry_skills = combine_industry_skills()
    combine_end_time = datetime.datetime.now()
    LOGGER.info(
        '[TAXONOMY] Time taken to combine jobs and skills data: %s',
        combine_end_time - combine_start_time
    )

    recommendations_start_time = datetime.datetime.now()
    LOGGER.info('[TAXONOMY] Started calculating Job recommendations.')
    jobs_with_recommendations = calculate_job_recommendations(all_job_and_skills)
    recommendations_end_time = datetime.datetime.now()

    LOGGER.info(
        '[TAXONOMY] Time taken to combine jobs and skills data: %s',
        recommendations_end_time - recommendations_start_time
    )

    start, page_size = 0, JOBS_PAGE_SIZE
    jobs = []
    LOGGER.info(f'[TAXONOMY] Started serializing Jobs data. Total Jobs: {qs.count()}')
    while qs[start:start + page_size].exists():
        job_serializer = JobSerializer(
            qs[start:start + page_size],
            many=True,
            context={
                'jobs_with_recommendations': jobs_with_recommendations,
                'industry_skills': industry_skills,
                'jobs_having_job_skills': get_job_ids(JobSkills.objects),
                'jobs_having_industry_skills': get_job_ids(IndustryJobSkill.objects),
            },
        )
        jobs.extend(job_serializer.data)
        start += page_size

    return jobs
