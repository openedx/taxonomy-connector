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


def get_job_query_filter(skills=None, industry=None):
    """
    Build job query filter to be used in fetching jobs data from the EMSI Service.

    Arguments:
        skills (list): jobs external ids to add in filter
        industry (Industry): Industry object to add in filter

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
        # for every skill's batch in our system (let say 50 skills) we are getting top 100 jobs by `unique_postings`
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
    if industry:
        jobs_query_filter['filter']['naics2'] = {
            'include': [str(industry.code)]
        }
        jobs_query_filter['rank']['limit'] = 25  # for every batch get top 25 jobs
        jobs_query_filter['nested_rank']['limit'] = 10  # for every job get top 10 skills
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

NAICS2_CODES = {
    11: 'Agriculture, Forest, Fishing and Hunting',
    21: 'Mining',
    22: 'Utilities',
    23: 'Construction',
    31: 'Manufacturing',
    32: 'Manufacturing',
    33: 'Manufacturing',
    42: 'Wholesale Trade',
    44: 'Retail Trade',
    45: 'Retail Trade',
    48: 'Transportation and Warehousing',
    49: 'Transportation and Warehousing',
    51: 'Information',
    52: 'Finance and Insurance',
    53: 'Real Estate and Rental and Leasing',
    54: 'Professional, Scientific, and Technical Services',
    55: 'Management of Companies and Enterprises',
    56: 'Administrative and Support and Waste Management and Redmediation Services',
    61: 'Educational Services',
    62: 'Health Care and Social Assistance',
    71: 'Arts, Entertainment, and Recreation',
    72: 'Accommodation and Food Services',
    81: 'Other Services (except Public Administration)',
    92: 'Public Administration',
}
