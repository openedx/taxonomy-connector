# -*- coding: utf-8 -*-
"""
Validator for course metadata provider.

All host platform must run this validator to make sure providers are working as expected.
"""
from taxonomy.providers.utils import get_program_metadata_provider


class ProgramMetadataProviderValidator:
    """
    Validate that the interface requirement for program metadata provider matches with the implementation.
    """

    def __init__(self, test_programs):
        """
        Setup an instance of program metadata provider.

        Since, these tests will run inside host application, list of test courses will also provided by the host.
        Args:
            test_programs (list<str>): List of program UUIDs in the form of string.
        """
        self.test_programs = test_programs
        self.program_metadata_provider = get_program_metadata_provider()

    def validate(self):
        """
        Validate ProgramMetadataProvider implements the interface as expected.

        Note: This is the only method that host platform will call,
        this method is responsible for calling the rest of the validation functions.
        """
        self.validate_get_programs()
        self.validate_get_all_programs()

    def validate_get_programs(self):
        """
        Validate `get_programs` methods has the correct interface implemented.
        """
        programs = self.program_metadata_provider.get_programs(self.test_programs)

        assert len(programs) == len(self.test_programs)

        for program in programs:
            assert 'uuid' in program
            assert 'title' in program
            assert 'subtitle' in program
            assert 'overview' in program

    def validate_get_all_programs(self):
        """
        Validate `get_all_programs` methods has the correct interface implemented.
        """
        programs = self.program_metadata_provider.get_all_programs()

        for program in programs:
            assert 'uuid' in program
            assert 'title' in program
            assert 'subtitle' in program
            assert 'overview' in program
