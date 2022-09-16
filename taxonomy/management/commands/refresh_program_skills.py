# -*- coding: utf-8 -*-
"""
Management command for refreshing the skills associated with programs.
"""
import logging

from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _

from taxonomy import utils
from taxonomy.choices import ProductTypes
from taxonomy.exceptions import ProgramMetadataNotFoundError, InvalidCommandOptionsError
from taxonomy.models import RefreshProgramSkillsConfig
from taxonomy.providers.utils import get_program_metadata_provider

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    """
        Command to refresh skills associated with the programs.

        Example usage:
            $ ./manage.py refresh_program_skills --program 'program1_uuid' --program 'program2_uuid' --commit
            $ # args-from-database means command line arguments will be picked from the database.
            $ ./manage.py refresh_program_skills --args-from-database
            $ # To update all the programs
            $ ./manage.py refresh_program_skills --all --commit
        """
    help = 'Refreshes the skills associated with programs.'
    product_type = ProductTypes.Program

    def add_arguments(self, parser):
        """
        Add arguments to the command parser.
        """
        parser.add_argument(
            '--program',
            metavar=_('UUID'),
            action='append',
            help=_('Program for mapping to skills.'),
            default=[],
        )
        parser.add_argument(
            '--args-from-database',
            action='store_true',
            help=_('Use arguments from the RefreshProgramSkillsConfig model instead of the command line.'),
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help=_('Create program skill mapping for all the programs.'),
        )
        parser.add_argument(
            '--commit',
            action='store_true',
            default=False,
            help=u'Commits the skills to storage. '
        )

    def get_args_from_database(self):
        """
        Return an options dictionary from the current RefreshProgramSkillsConfig model.
        """
        config = RefreshProgramSkillsConfig.get_solo()
        argv = config.arguments.split()
        parser = self.create_parser('manage.py', 'refresh_program_skills')
        return parser.parse_args(argv).__dict__

    def handle(self, *args, **options):
        """
        Entry point for management command execution
        """
        if not (options['args_from_database'] or options['all'] or options['program']):
            raise InvalidCommandOptionsError('Either program, args_from_database or all argument must be provided.')

        if options['args_from_database']:
            options = self.get_args_from_database()

        LOGGER.info('[TAXONOMY] Refresh Program Skills. Options: [%s]', options)

        if options['all']:
            programs = get_program_metadata_provider().get_all_programs()
        elif options['program']:
            programs = get_program_metadata_provider().get_programs(program_ids=options['program'])
            if not programs:
                raise ProgramMetadataNotFoundError(
                    'No program metadata was found for following programs. {}'.format(options['program'])
                )
        else:
            raise InvalidCommandOptionsError('Either program or all argument must be provided.')

        LOGGER.info('[TAXONOMY] Refresh program skills process started.')
        utils.refresh_product_skills(programs, options['commit'], self.product_type)
