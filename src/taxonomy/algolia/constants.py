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
        'searchable(industry_names)',
        'searchable(b2c_opt_in)',
        'searchable(job_sources)',
        'filterOnly(metadata_language)',
    ],
    'customRanking': [
        # Use a numeric priority field so English (0) always ranks above
        # translated records (1), regardless of language code alphabetic order
        # (e.g., Arabic 'ar' would otherwise rank higher than English 'en').
        'asc(language_sort_priority)',
    ],
}

JOBS_PAGE_SIZE = 1000

# This is the maximum number of objects that should be embedded inside an algolia record.
EMBEDDED_OBJECT_LENGTH_CAP = 20

# External ID of all the jobs that should not be indexed on algolia.
JOBS_TO_IGNORE = [
    'ET0000000000000000',  # 'Unclassified' job
]

# Default enabled locales for localized Algolia job records.
# Override per environment using Django setting: TAXONOMY_TRANSLATION_LOCALES.
TAXONOMY_TRANSLATION_LOCALES = ['es']
