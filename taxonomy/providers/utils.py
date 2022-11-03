# -*- coding: utf-8 -*-
"""
Taxonomy providers are configured via django settings.

A map for different providers and their django setting is provided here
    1. Course Metadata Provider: TAXONOMY_COURSE_METADATA_PROVIDER

This file provides functions to load the provider class and makes it available to be used by taxonomy.
"""

from django.conf import settings
from django.utils.module_loading import import_string


def get_course_metadata_provider(*args, **kwargs):
    """
    Load and return an instance of course metadata provider.

    Load course metadata provider class through `TAXONOMY_COURSE_METADATA_PROVIDER`, instantiate it using
    the `*args` and `**kwargs` provided in the function arguments and return the instance.
    """
    return import_string(settings.TAXONOMY_COURSE_METADATA_PROVIDER)(*args, **kwargs)


def get_program_metadata_provider(*args, **kwargs):
    """
    Load and return an instance of program metadata provider.

    Load program provider class through `TAXONOMY_PROGRAM_METADATA_PROVIDER`, instantiate it using
    the `*args` and `**kwargs` provided in the function arguments and return the instance.
    """
    return import_string(settings.TAXONOMY_PROGRAM_METADATA_PROVIDER)(*args, **kwargs)


def get_xblock_metadata_provider(*args, **kwargs):
    """
    Load and return an instance of xblock metadata provider.

    Load xblock metadata provider class through `TAXONOMY_XBLOCK_METADATA_PROVIDER`, instantiate it using
    the `*args` and `**kwargs` provided in the function arguments and return the instance.
    """
    return import_string(settings.TAXONOMY_XBLOCK_METADATA_PROVIDER)(*args, **kwargs)
