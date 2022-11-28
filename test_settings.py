# -*- coding: utf-8 -*-
"""
These settings are here to use during tests, because django requires them.

In a real-world use case, apps in this project are installed into other
Django applications, so these settings will not be used.
"""

import os
from os.path import abspath, dirname, join

from celery import Celery


def root(*args):
    """
    Get the absolute path of the given path relative to the project root.
    """
    return join(abspath(dirname(__file__)), *args)


DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DB_MIGRATION_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.environ.get('DB_MIGRATION_NAME', 'default.db'),
        'USER': os.environ.get('DB_MIGRATION_USER', ''),
        'PASSWORD': os.environ.get('DB_MIGRATION_PASSWORD', ''),
        'HOST': os.environ.get('DB_MIGRATION_HOST', ''),
        'PORT': os.environ.get('DB_MIGRATION_PORT', ''),
    }
}

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'taxonomy',
)

LOCALE_PATHS = [
    root('taxonomy', 'conf', 'locale'),
]

ROOT_URLCONF = 'taxonomy.urls'

SECRET_KEY = 'insecure-secret-key'

MIDDLEWARE = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.sites.middleware.CurrentSiteMiddleware',
)

# Settings related to to EMSI client
# API URLs are altered to avoid accidentally calling the API in tests
# Original URL: https://auth.emsicloud.com/connect/token
EMSI_API_ACCESS_TOKEN_URL = 'https://auth.emsicloud.com/connect/token'

# Original URL: https://emsiservices.com
EMSI_API_BASE_URL = 'http://example.com'
EMSI_CLIENT_ID = 'test-client'
EMSI_CLIENT_SECRET = 'test-secret'

TAXONOMY_COURSE_METADATA_PROVIDER = 'test_utils.providers.DiscoveryCourseMetadataProvider'
TAXONOMY_PROGRAM_METADATA_PROVIDER = 'test_utils.providers.DiscoveryProgramMetadataProvider'
TAXONOMY_XBLOCK_METADATA_PROVIDER = 'test_utils.providers.DiscoveryXBlockMetadataProvider'

### CELERY

app = Celery('taxonomy')  # pylint: disable=invalid-name
app.config_from_object('django.conf:settings', namespace="CELERY")

CELERY_TASK_ALWAYS_EAGER = True

# In memory broker for tests
CELERY_BROKER_URL = 'memory://localhost/'

### END CELERY

ALGOLIA = {
    'APPLICATION_ID': '',
    'API_KEY': '',
    'TAXONOMY_INDEX_NAME': ''
}

MIN_VOTES_FOR_SKILLS = 2
RATIO_THRESHOLD_FOR_SKILLS = 0.5
