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
                                'name': 'Nunchuks',
                                'significance': 9.3498822,
                                'unique_postings': 25
                            },
                            {
                                'name': 'Swift (Programming Language)',
                                'significance': 8.390285,
                                'unique_postings': 1337
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
                                'name': 'Social Media Marketing',
                                'significance': 4.292374,
                                'unique_postings': 150
                            },
                            {
                                'name': 'Bowhunting',
                                'significance': 2.3938203,
                                'unique_postings': 42
                            }
                        ]
                    }
                }
            ]
        }
    }
}
