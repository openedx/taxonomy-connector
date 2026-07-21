# -*- coding: utf-8 -*-
"""
Taxonomy Service is the django app that can be installed in any project.

By implementing the interfaces required by this service this app can be used by any project.
Main interfaces are data providers and can be found in `taxonomy/providers/` directory.
The purpose of this service is to aggregate skills taxonomy data for edx platform, this is done by aggregating course
data like course title, description etc. and then, for skills, calling the EMSI API that returns skills taxonomy for
each course based on its description, title etc.
"""
