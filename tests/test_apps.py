# -*- coding: utf-8 -*-
"""
Tests for the `taxonomy-connector` app.
"""

import taxonomy
from test_utils.testcase import TaxonomyTestCase


class TestTaxonomyConfigConfig(TaxonomyTestCase):
    """
    Validate taxonomy app configuration.
    """

    def setUp(self):
        """
        Set up test environment.
        """
        super(TestTaxonomyConfigConfig, self).setUp()
        self.app_config = taxonomy.apps.TaxonomyConfig(
            'taxonomy', taxonomy
        )

    def test_name(self):
        """
        Validate app config for taxonomy is setup correctly.
        """
        assert self.app_config.name == 'taxonomy'
