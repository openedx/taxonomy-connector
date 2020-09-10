# -*- coding: utf-8 -*-
"""
Sample responses for salary data from EMSI service. These will be used in tests.
"""

JOB_POSTINGS_FILTER = {
    'filter': {
        'when': {
            'start': '2016-01',
            'end': '2018-03',
            'type': 'expired'
        },
        'naics2': [
            54
        ],
        'naics3': [
            541
        ],
        'naics4': [
            5412
        ],
        'naics5': [
            54121
        ],
        'naics6': [
            541213
        ],
        'edulevels': [
            0
        ],
        'edulevels_name': [
            'High school or GED'
        ]
    },
    'rank': {
        'by': 'unique_postings',
        'limit': 20,
        'extra_metrics': [
            'duplicate_postings',
            'median_posting_duration'
        ]
    }
}

JOB_POSTINGS = {
    'data': {
        'totals': {
            'median_posting_duration': 21,
            'unique_postings': 1646,
            'duplicate_postings': 5551
        },
        'ranking': {
            'facet': 'title_name',
            'rank_by': 'unique_postings',
            'limit': 10,
            'buckets': [
                {
                    'median_salary': 87424.78,
                    'median_posting_duration': 25,
                    'name': 'Senior Software Engineer',
                    'unique_postings': 1043,
                    'unique_companies': 229
                },
                {
                    'median_salary': '34000.00',
                    'median_posting_duration': '15',
                    'name': 'Software Engineer',
                    'unique_postings': '603',
                    'unique_companies': '500'
                },
                {
                    'median_salary': '$45000.34',
                    'median_posting_duration': 28,
                    'name': 'Insurance Sales Agent',
                    'unique_postings': 1400,
                    'unique_companies': 960
                },

            ]
        }
    }
}

MISSING_MEDIAN_SALARY_JOB_POSTING = {
    'data': {
        'ranking': {
            'facet': 'title_name',
            'rank_by': 'unique_postings',
            'limit': 10,
            'buckets': [
                {
                    'median_posting_duration': 25,
                    'name': 'Senior Software Engineer',
                    'unique_postings': 1043,
                    'unique_companies': 229
                },
            ]
        }
    }
}
