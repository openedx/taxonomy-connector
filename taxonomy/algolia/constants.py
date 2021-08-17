# -*- coding: utf-8 -*-
"""
Constants for algolia.
"""
# default configuration for the index
ALGOLIA_JOBS_INDEX_SETTINGS = {
    'attributeForDistinct': 'external_id',
    'distinct': True,
    'typoTolerance': False,
    'searchableAttributes': [
        'unordered(name)',
        'skills.name',
    ],
    'attributesForFaceting': [
        'searchable(name)',
        'searchable(skills.name)',
    ],
}

JOBS_PAGE_SIZE = 1
