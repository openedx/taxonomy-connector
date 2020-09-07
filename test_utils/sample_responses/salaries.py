SALARIES_FILTER = {
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

SALARIES = {
    'data': {
        'totals': {
            'median_posting_duration': 21,
            'unique_postings': 1646,
            'duplicate_postings': 5551
        },
        'ranking': {
            'facet': 'company',
            'rank_by': 'unique_postings',
            'limit': 10,
            'buckets': [
                {
                    'median_posting_duration': 25,
                    'name': 'Apple Inc.',
                    'unique_postings': 1043,
                    'duplicate_postings': 2049
                },
                {
                    'median_posting_duration': 15,
                    'name': 'Facebook',
                    'unique_postings': 603,
                    'duplicate_postings': 3502
                }
            ]
        }
    }
}
