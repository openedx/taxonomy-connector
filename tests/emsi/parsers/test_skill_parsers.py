# -*- coding: utf-8 -*-
"""
Tests for the `taxonomy-connector` emsi data parsers.
"""
import ddt

from taxonomy.emsi.parsers.skill_parsers import SkillDataParser
from test_utils.testcase import TaxonomyTestCase


@ddt.ddt
class TestSkillDataParser(TaxonomyTestCase):
    """
    Validate the behavior of skill data parsers.
    """

    @ddt.data(
        (
            {'data': {'category': None, 'subcategory': None}},
            {'category': None, 'subcategory': None},
        ),
        (
            {'data': {'category': None, 'subcategory': {'id': 'test', 'name': 'test'}}},
            {'category': None, 'subcategory': None},
        ),
        (
            {'data': {'category': {'id': 'test', 'name': 'test'}, 'subcategory': None}},
            {'category': {'id': 'test', 'name': 'test'}, 'subcategory': None},
        ),
        (
            {'data': {'category': {'id': 'test', 'name': 'test'}, 'subcategory': {'id': 'test', 'name': 'test'}}},
            {'category': {'id': 'test', 'name': 'test'}, 'subcategory': {'id': 'test', 'name': 'test'}},
        ),

        # Now test cases where values are not valid
        (
            {'data': {'category': {'id': 'test', 'name': 'null'}, 'subcategory': {'id': 'test', 'name': 'test'}}},
            {'category': None, 'subcategory': None},
        ),
        (
            {'data': {'category': {'id': 'test', 'name': 'None'}, 'subcategory': {'id': 'test', 'name': 'test'}}},
            {'category': None, 'subcategory': None},
        ),
        (
            {'data': {'category': {'id': 'test', 'name': None}, 'subcategory': {'id': 'test', 'name': 'test'}}},
            {'category': None, 'subcategory': None},
        ),
        (
            {'data': {'category': {'id': 'test', 'name': ''}, 'subcategory': {'id': 'test', 'name': 'test'}}},
            {'category': None, 'subcategory': None},
        ),
        (
            {'data': {'category': {'id': 'test', 'name': 'test'}, 'subcategory': {'id': 'test', 'name': 'NULL'}}},
            {'category': {'id': 'test', 'name': 'test'}, 'subcategory': None},
        ),
        (
            {'data': {'category': {'id': 'test', 'name': 'test'}, 'subcategory': {'id': 'test', 'name': 'NONE'}}},
            {'category': {'id': 'test', 'name': 'test'}, 'subcategory': None},
        ),
        (
            {'data': {'category': {'id': 'test', 'name': 'test'}, 'subcategory': {'id': 'test', 'name': None}}},
            {'category': {'id': 'test', 'name': 'test'}, 'subcategory': None},
        ),
        (
            {'data': {'category': {'id': 'test', 'name': 'test'}, 'subcategory': {'id': 'test', 'name': ''}}},
            {'category': {'id': 'test', 'name': 'test'}, 'subcategory': None},
        ),
    )
    @ddt.unpack
    def test_get_skill_category_data(self, sample_data, expected_data):
        """
        Validate the behavior of get_skill_category_data inside SkillDataParser.
        """
        parser = SkillDataParser(sample_data)

        assert parser.get_skill_category_data() == expected_data
