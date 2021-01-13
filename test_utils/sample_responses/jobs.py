# -*- coding: utf-8 -*-
"""
Sample responses for jobs data from EMSI service. These will be used in tests.
"""

JOBS_FILTER = {
    'filter': {
        'when': {
            'start': '2016-01',
            'end': '2018-03',
            'type': 'active',
        },
        'company': ['NCbe94c8a6-b7a0-4853-bf67-221889b26487'],
        'company_name': {'include': ['Uber Technologies, Inc.']},
        'posting_duration': {'lower_bound': 0, 'upper_bound': 100},
    },
    'rank': {
        'by': 'unique_postings',
        'limit': 5,
        'extra_metrics': ['duplicate_postings', 'median_posting_duration'],
    },
    'nested_rank': {'by': 'significance', 'min_unique_postings': 1, 'limit': 5},
}

JOBS = {
    'data': {
        'totals': {
            'median_posting_duration': 36,
            'unique_postings': 1646,
            'duplicate_postings': 5551
        },
        'ranking': {
            'facet': 'company',
            'rank_by': 'unique_postings',
            'limit': 2,
            'buckets': [
                {
                    'median_posting_duration': 22,
                    'name': 'Apple Inc.',
                    'unique_postings': 1043,
                    'duplicate_postings': 2049,
                    'ranking': {
                        'facet': 'skills',
                        'rank_by': 'significance',
                        'limit': 2,
                        'buckets': [
                            {
                                'name': 'KS1208078SN0KY08W3QT',
                                'significance': 31.394078320130294,
                                'unique_postings': 25953
                            },
                            {
                                'name': 'KS1274Y5Z0PFK7XN155K',
                                'significance': 21.08851543427918,
                                'unique_postings': 34705
                            }
                        ]
                    }
                },
                {
                    'median_posting_duration': 21,
                    'name': 'Facebook',
                    'unique_postings': 603,
                    'duplicate_postings': 3502,
                    'ranking': {
                        'facet': 'skills',
                        'rank_by': 'significance',
                        'limit': 2,
                        'buckets': [
                            {
                                'name': 'KS1283V6XDFZSK6YP0HF',
                                'significance': 58.91321355889151,
                                'unique_postings': 150
                            },
                            {
                                'name': 'ESEB1D4619E6E83A061D',
                                'significance': 14.426926671377828,
                                'unique_postings': 42
                            }
                        ]
                    }
                }
            ]
        }
    }
}
