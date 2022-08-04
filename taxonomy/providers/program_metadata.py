# -*- coding: utf-8 -*-
"""
Abstract base class for program metadata providers.

All host platform must implement this provider in order for taxonomy to work.
"""
from abc import abstractmethod


class ProgramMetadataProvider:
    """
    Abstract base class for program providers.

    All abstract methods must be implemented for taxonomy's normal functionality.
    """

    @abstractmethod
    def get_programs(self, program_ids):
        """
        Get a list of programs matching the program ids provided in the argument.

        Arguments:
          program_ids(list<str>): A list of UUIDs in the form of a string.

        Returns:
          list<dict>: A list of program in the form of dictionary.
            Dictionary object must have the following keys
            1. uuid: Program UUID
            2. title: Program title
            3. subtitle: Program subtitle
            4. overview: Program overview
        """

    @abstractmethod
    def get_all_programs(self):
        """
        Get iterator for all the programs.

        Returns:
          iterator<dict>: An iterator of programs in the form of dictionary.
            Dictionary object must have the following keys
            1. uuid: Program UUID
            2. title: Program title
            3. subtitle: Program subtitle
            4. overview: Program overview
        """
