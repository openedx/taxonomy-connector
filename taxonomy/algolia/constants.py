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

# This is the the maximum number of objects that should be embedded inside an algolia record.
EMBEDDED_OBJECT_LENGTH_CAP = 20
