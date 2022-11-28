# -*- coding: utf-8 -*-
"""
Validator for xblock metadata provider.

All host platform must run this validator to make sure providers are working as expected.
"""
from taxonomy.providers.utils import get_xblock_metadata_provider
from taxonomy.providers import XBlockContent


class XBlockMetadataProviderValidator:
    """
    Validate that the interface requirement for xblock metadata provider matches with the implementation.
    """

    def __init__(self, test_xblocks):
        """
        Setup an instance of xblock metadata provider.

        Since, these tests will run inside host application, list of test xblocks will also provided by the host.
        Args:
            test_xblocks (list<str>): List of xblock UUIDs in the form of string.
        """
        self.test_xblocks = test_xblocks
        self.xblock_metadata_provider = get_xblock_metadata_provider()

    def validate(self):
        """
        Validate XBlockMetadataProvider implements the interface as expected.

        Note: This is the only method that host platform will call,
        this method is responsible for calling the rest of the validation functions.
        """
        self.validate_get_xblocks()
        self.validate_get_all_xblocks_in_course()

    def validate_get_xblocks(self):
        """
        Validate `get_xblocks` methods has the correct interface implemented.
        """
        xblocks = self.xblock_metadata_provider.get_xblocks(self.test_xblocks)

        assert len(xblocks) == len(self.test_xblocks)

        for xblock in xblocks:
            assert isinstance(xblock, XBlockContent)

    def validate_get_all_xblocks_in_course(self):
        """
        Validate `get_all_xblocks_in_course` methods has the correct interface implemented.
        """
        xblocks = self.xblock_metadata_provider.get_all_xblocks_in_course('dummy-course-id')

        for xblock in xblocks:
            assert isinstance(xblock, XBlockContent)
