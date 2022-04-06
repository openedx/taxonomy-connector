# -*- coding: utf-8 -*-
"""
Constants used by the taxonomy connector.
"""

from datetime import date

from dateutil.relativedelta import relativedelta


def get_lookup_query_filter(external_ids):
    """
    Build query filter for the lookup endpoint.
    """
    lookup_query_filter = {
        'ids': external_ids
    }
    return lookup_query_filter


def get_job_query_filter(skills=None):
    """
    Build job query filter to be used in fetching jobs data from the EMSI Service.

    Arguments:
        skills (list): jobs external ids to add in filter

    Returns:
        dict: Job postings query filter to used in EMSI API
    """
    jobs_query_filter = {
        'filter': {
            'when': {
                'start': str(date.today() - relativedelta(months=6)),
                'end': str(date.today()),
                'type': 'active'
            },
        },
        # we are using TITLE facet for `rank` and SKILLS facet for the `nested rank`
        # for every skills batch in our system (let say 100 skills) we are getting top 100 jobs by `unique_postings`
        # and 10 skills per every job ranked by significance.
        'rank': {   # jobs
            'by': 'unique_postings',
            'limit': 100  # rank.limit for nested rankings must be <= 100
        },
        'nested_rank': {  # skills
            'by': 'significance',
            'limit': 10  # nested_rank.limit for nested rankings must be <= 1000
        }
    }
    if skills:
        jobs_query_filter['filter']['skills'] = {
            'include': skills,
            'include_op': 'or'
        }
    return jobs_query_filter


def get_job_posting_query_filter(jobs=None):
    """
    Build job  query filter to be used in fetching jobs posting data from the EMSI Service.

    Arguments:
        jobs (list): jobs external ids to add in filter

    Returns:
        dict: Job postings query filter to used in EMSI API
    """
    job_posting_query_filter = {
        'filter': {
            'when': {
                'start': str(date.today() - relativedelta(months=6)),
                'end': str(date.today()),
                'type': 'active'
            }
        },
        # We are using TITLE facet for `rank` and for every job batch in our system (let say 100 job)
        # we are getting jobpostings by `unique_postings` with max limit to 1000.
        # There is always one JobPosting against each job we pass to the API.
        'rank': {
            'by': 'unique_postings',
            'limit': 1000,   # rank.limit must be <= 1000
            'extra_metrics': [
                'median_posting_duration',
                'median_salary',
                'unique_companies'
            ]
        }
    }
    if jobs:
        job_posting_query_filter['filter']['title'] = {
            'include': jobs,
            'include_op': 'or'
        }
    return job_posting_query_filter


AMAZON_TRANSLATION_ALLOWED_SIZE = 5000
EMSI_API_RATE_LIMIT_PER_SEC = 5
TRANSLATE_SERVICE = 'translate'
ENGLISH = 'en'
AUTO = 'auto'
REGION = 'us-east-1'
