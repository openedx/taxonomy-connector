# -*- coding: utf-8 -*-
"""
Constants used by the taxonomy connector.
"""

from datetime import date

from dateutil.relativedelta import relativedelta

JOBS_QUERY_FILTER = {
    'filter': {
        'when': {
            'start': str(date.today() - relativedelta(months=6)),
            'end': str(date.today()),
            'type': 'active'
        },
    },
    'rank': {
        'by': 'unique_postings',
    },
    'nested_rank': {
        'by': 'significance',
    }
}

JOB_POSTINGS_QUERY_FILTER = {
    'filter': {
        'when': {
            'start': str(date.today() - relativedelta(months=6)),
            'end': str(date.today()),
            'type': 'active'
        }
    },
    'rank': {
        'by': 'unique_postings',
        'extra_metrics': [
            'median_posting_duration',
            'median_salary',
            'unique_companies'
        ]
    }
}
