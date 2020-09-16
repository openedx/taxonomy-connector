# -*- coding: utf-8 -*-
"""
Constants used by the taxonomy service.
"""

JOBS_QUERY_FILTER = {
    'filter': {
        'when': {
            'start': '2020-01',
            'end': '2020-06',
            'type': 'active'
        },
        'posting_duration': {
            'lower_bound': 0,
            'upper_bound': 90
        }
    },
    'rank': {
        'by': 'unique_postings',
        'min_unique_postings': 1000,
        'limit': 20
    },
    'nested_rank': {
        'by': 'significance',
        'limit': 10
    }
}

JOB_POSTINGS_QUERY_FILTER = {
    'filter': {
        'when': {
            'start': '2020-01',
            'end': '2020-06',
            'type': 'active'
        },
        'posting_duration': {
            'lower_bound': 0,
            'upper_bound': 90
        }
    },
    'rank': {
        'by': 'unique_postings',
        'min_unique_postings': 1000,
        'limit': 20,
        'extra_metrics': [
            'median_posting_duration',
            'median_salary',
            'unique_companies'
        ]
    }
}
