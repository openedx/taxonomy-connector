"""
Module that contains utility methods and classes for parsing EMSI responses.
"""
INVALID_NAMES = {'NULL', 'NONE', ''}


class SkillDataParser:
    """
    Parser for processing/parsing EMSI responses returned by the skills API (https://api.emsidata.com/apis/skills).
    """
    def __init__(self, response):
        """
        Initialise the parser using API response object

        Arguments:
            response (dict): A dictionary containing the API response from skills API.
                response dict should contain `data` key as the top level key.
        """
        self.data = response['data']

    def get_skill_category_data(self):
        """
        Parse and return category and subcategory data from the response dict.

        Returns:
            (dict): A dictionary containing at-least following 2 keys
                1. category  -> value against this key will be a dict containing `id` and `name`.
                2. subcategory -> value against this key will be a dict containing `id` and `name`.
        """
        category = self.data.get('category')
        subcategory = self.data.get('subcategory')

        if category is None or category.get('name') is None or category.get('name').upper() in INVALID_NAMES:
            category = None
            subcategory = None  # We can not have a non-null subcategory with null category.
        elif subcategory is None or subcategory.get('name') is None or subcategory.get('name').upper() in INVALID_NAMES:
            subcategory = None

        return {
            'category': category,
            'subcategory': subcategory,
        }
