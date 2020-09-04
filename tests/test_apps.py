# -*- coding: utf-8 -*-
"""
Tests for the `taxonomy-service` app.
"""

import taxonomy
from test_utils.testcase import TaxonomyTestCase


class TestTaxonomyConfigConfig(TaxonomyTestCase):
    """
    Test taxonomy app config.
    """

    def setUp(self):
        """
        Set up test environment
        """
        super(TestTaxonomyConfigConfig, self).setUp()
        self.app_config = taxonomy.apps.TaxonomyConfig(
            'taxonomy', taxonomy
        )

    def test_name(self):
        assert self.app_config.name == 'taxonomy'
