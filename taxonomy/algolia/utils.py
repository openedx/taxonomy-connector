# -*- coding: utf-8 -*-
"""
Utility functions related to algolia indexing.
"""
import logging
import datetime
import pandas as pd

from django.conf import settings
from django.db.models import Sum

from taxonomy.algolia.client import AlgoliaClient
from taxonomy.algolia.constants import ALGOLIA_JOBS_INDEX_SETTINGS, JOBS_PAGE_SIZE, EMBEDDED_OBJECT_LENGTH_CAP
from taxonomy.algolia.serializers import JobSerializer
from taxonomy.models import Job, Industry, JobSkills, IndustryJobSkill

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


def calculate_jaccard_similarity(set_a, set_b):
    """
    Calculate Jaccard similarity between two sets of job skills.
    """
    try:
        intersection = set_a.intersection(set_b)
        jaccard_similarity = len(intersection) / len(set_a.union(set_b))
        return jaccard_similarity
    except ZeroDivisionError:
        return float(0)


def fetch_job_skills(job, all_job_skills):
    """
    Construct a list of all the job skills from the database.

    Returns:
        (list<dict>): A list of dicts containing job skills data.
    """
    job_skills = all_job_skills.filter(job=job)
    skills = []
    for job_skill in job_skills:
        skills.append(job_skill.skill.name)
    return skills


def combine_jobs_and_skills_data(jobs):
    """
    Combine jobs and skills data.

    Returns:
        (list<dict>): A list of dicts containing job and their skills in a list.
    """
    jobs = jobs.all()
    all_job_skills = JobSkills.objects.all()

    all_job_and_skills_data = []
    for job in jobs:
        all_job_skills = JobSkills.objects.filter(job=job)
        skills = fetch_job_skills(job, all_job_skills)
        all_job_and_skills_data.append({
            'name': job.name,
            'skills': skills,
        })

    return all_job_and_skills_data


def calculate_job_recommendations(jobs):
    """
    Calculate job recommendations.

    Args:
        job (list<dict>): AA list of dicts containing job and their skills in a list.

    Returns:
        (list<dict>): A list of dicts containing jobs and their recommended jobs.
    """
    candidate_jobs = []
    matching_jobs = []
    jaccard_similarities = []

    for job in jobs:
        job_skills_set = set(job['skills'])

        for candidate_job in jobs:
            if job['name'] == candidate_job['name']:
                continue

            other_job_skills_set = set(candidate_job['skills'])
            jaccard_similarity = calculate_jaccard_similarity(job_skills_set, other_job_skills_set)
            candidate_jobs.append(job['name'])
            matching_jobs.append(candidate_job['name'])
            jaccard_similarities.append(jaccard_similarity)

    similar_jobs = pd.DataFrame({
        'job': candidate_jobs,
        'matching_job': matching_jobs,
        'jaccard_similarity': jaccard_similarities,
    })

    similar_jobs['rank'] = similar_jobs.groupby('job')['jaccard_similarity'].rank(method='first', ascending=False)
    mask = (similar_jobs['rank'] <= 3)
    similar_jobs = similar_jobs[mask].sort_values(by=['job', 'rank'], ascending=[True, True])

    jobs_and_recommendations = []
    for job in jobs:
        jobs_and_recommendations.append({
            'name': job['name'],
            'similar_jobs': similar_jobs[similar_jobs['job'] == job['name']]['matching_job'].tolist(),
        })
    return jobs_and_recommendations


def combine_industry_skills():
    """
    Constructs a dict with keys as industry names and values as their skills.
    """
    industries = list(Industry.objects.all())
    industries_and_skills = {}
    for industry in industries:
        # sum all significances for the same skill and then sort on total significance
        skills = list(
            IndustryJobSkill.objects.filter(industry=industry).values_list('skill__name', flat=True).annotate(
                total_significance=Sum('significance')).order_by('-total_significance').distinct()[
                    :EMBEDDED_OBJECT_LENGTH_CAP]
        )
        industries_and_skills[industry.name] = skills
    return industries_and_skills


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
                'industry_skills': industry_skills
            },
        )
        jobs.extend(job_serializer.data)
        start += page_size

    return jobs
