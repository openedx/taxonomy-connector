# -*- coding: utf-8 -*-
"""
Initialization code for taxonomy application.
"""
from __future__ import unicode_literals

import logging

from django.apps import AppConfig

LOGGER = logging.getLogger(__name__)


class TaxonomyConfig(AppConfig):
    """
    App configuration for taxonomy app.
    """

    name = 'taxonomy'

    def ready(self):
        """
        Connect handlers to signals.
        """
        from .signals import handlers  # pylint: disable=unused-import,import-outside-toplevel
