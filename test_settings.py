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
    'django.contrib.admin',
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

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'DIRS': (
            root('templates'),
        ),
        'OPTIONS': {
            'context_processors': (
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
            ),
            'debug': True,  # Django will only display debug pages if the global DEBUG setting is set to True.
        }
    },
]
# Settings related to LightCast (EMSI) client
# API URLs are altered to avoid accidentally calling the API in tests
# Original URL: https://auth.emsicloud.com/connect/token
EMSI_API_ACCESS_TOKEN_URL = 'https://auth.emsicloud.com/connect/token'

# Original URL: https://emsiservices.com
EMSI_API_BASE_URL = 'http://example.com'
EMSI_CLIENT_ID = 'test-client'
EMSI_CLIENT_SECRET = 'test-secret'

TAXONOMY_COURSE_METADATA_PROVIDER = 'test_utils.providers.DiscoveryCourseMetadataProvider'
TAXONOMY_COURSE_RUN_METADATA_PROVIDER = 'test_utils.providers.DiscoveryCourseRunMetadataProvider'
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

SKILLS_VERIFICATION_THRESHOLD = 2
SKILLS_VERIFICATION_RATIO_THRESHOLD = 0.5
SKILLS_IGNORED_THRESHOLD = 10
SKILLS_IGNORED_RATIO_THRESHOLD = 0.8

XPERT_AI_API_V2 = 'http://test.chat.ai/v2'
XPERT_AI_CLIENT_ID = 'test client id'
XPERT_JOB_DESCRIPTION_SYSTEM_MESSAGE = 'test system prompt'
XPERT_JOB_TO_JOB_SYSTEM_MESSAGE = 'test system prompt'

JOB_DESCRIPTION_PROMPT = 'Generate a description for {job_name} job role.'
JOB_TO_JOB_DESCRIPTION_PROMPT = 'How can a {current_job_name} switch to {future_job_name} job role.'
