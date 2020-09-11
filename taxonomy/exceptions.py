# -*- coding: utf-8 -*-
"""
Exceptions that will be used by the taxonomy service to indicate different errors.
"""


class TaxonomyServiceAPIError(Exception):
    """
    Exception to raise when something goes wrong while talking to the EMSI service.
    """
