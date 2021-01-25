# -*- coding: utf-8 -*-
"""
Taxonomy Service is the django app that can be installed in any project.

By implementing the interfaces required by this service this app can be used by any project.
Main interfaces are data providers and can be found in `taxonomy/providers/` directory.
The purpose of this service is to aggregate skills taxonomy data for edx platform, this is done by aggregating course
data like course title, description etc. and then, for skills, calling the EMSI API that returns skills taxonomy for
each course based on its description, title etc.
"""

# taxonomy service follows semantic versioning specifications,
# A version number is of the form `MAJOR.MINOR.PATCH`, where
# 1. MAJOR version when you make incompatible API changes,
# 2. MINOR version when you add functionality in a backwards compatible manner, and
# 3. PATCH version when you make backwards compatible bug fixes.
# More details can be found at https://semver.org/
__version__ = '1.3.1'

default_app_config = 'taxonomy.apps.TaxonomyConfig'  # pylint: disable=invalid-name
