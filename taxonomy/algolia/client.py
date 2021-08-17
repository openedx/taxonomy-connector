# -*- coding: utf-8 -*-
"""
Algolia api client code.
"""

import logging

from algoliasearch import algoliasearch

LOGGER = logging.getLogger(__name__)


class AlgoliaClient:
    """
    Client to handle algolia index.

    This provides implementation for the common operations such as index initialization, index settings updates,
    data indexing etc.
    """
    def __init__(self, application_id, api_key, index_name):
        """
        Initialize the client with application id, api key and index name.

        Arguments:
            application_id (str): Algolia Application id
            api_key (str): Algolia API key
            index_name (str): Name of the index this client instance will be managing.
        """
        self._client = algoliasearch.Client(application_id, api_key)
        self.algolia_index = self._client.init_index(index_name)

    def set_index_settings(self, index_settings):
        """
        Set default settings to use for the Algolia index.

        Note: This will override manual updates to the index configuration on the
        Algolia dashboard but ensures consistent settings (configuration as code).

        Arguments:
            index_settings (dict): A dictionary of Algolia settings.
        """
        self.algolia_index.set_settings(index_settings)

    def replace_all_objects(self, algolia_objects):
        """
        Clears all objects from the index and replaces them with a new set of objects. The records are
        replaced in the index without any downtime due to an atomic reindex.

        See https://www.algolia.com/doc/api-reference/api-methods/replace-all-objects/ for more details.

        Arguments:
            algolia_objects (list<dict>): List of dicts to include in the Algolia index.
        """
        request_options = algoliasearch.RequestOptions({
            'safe': True,  # wait for asynchronous indexing operations to complete
        })
        self.algolia_index.replace_all_objects(algolia_objects, request_options)
        LOGGER.info(
            '[TAXONOMY] The %s Algolia index was successfully indexed with %s objects.',
            self.algolia_index.index_name,
            len(algolia_objects),
        )
