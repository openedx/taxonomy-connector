# -*- coding: utf-8 -*-
"""
Exceptions that will be used by the taxonomy connector to indicate different errors.
"""


class TaxonomyAPIError(Exception):
    """
    Exception to raise when something goes wrong while talking to the EMSI service.
    """
