Taxonomy
========

.. image:: https://img.shields.io/pypi/v/taxonomy-connector.svg
    :target: https://pypi.org/project/taxonomy-connector/
    :alt: PyPI

.. image:: http://codecov.io/github/edx/taxonomy-connector/coverage.svg?branch=master
    :target: http://codecov.io/github/edx/taxonomy-connector?branch=master
    :alt: Codecov
    
.. image:: https://github.com/edx/taxonomy-connector/workflows/Python%20CI/badge.svg?branch=master
    :target: https://github.com/edx/taxonomy-connector/actions?query=workflow%3A%22Python+CI%22
    :alt: CI

The taxonomy service is a library that can be installed in other edX components
that provides access to third party taxonomy vendors. EMSI is currently the
only vendor available, but others may be integrated as necessary. This service
can communicate with the vendor to get job, skill, and salary data. This service
can also be used to submit data (course descriptions, etc.) to the vendor to
produce potential matches for a skill or job.

After submitting a pull request, please use the Github "Reviewers" widget to add
relevant reviewers and track review process.


Getting Started
---------------

To install ``taxonomy-connector``, for example, in Course Discovery, follow these steps:

#. It is recommended that you clone this repo into a sub-folder of your working directory. Create a sub-folder with name ``src`` if it doesn't already exist.
#. Clone this repository into the ``src`` folder.
#. Go to the shell of the host environment where you want to install this package and run this ``pip install -e /edx/src/taxonomy-connector``
#. Changes made into the taxonomy repository will now be picked up by your host environment.


Notes:

- In order to communicate with EMSI service, you need to set the values of ``client_id`` and ``client_secret``. These values are picked up from the host environment so you need to pass them in ``.yaml`` file of the host environment.
- Also, to make taxonomy work, the host platform must add an implementation of data providers written in ``./taxonomy/providers``
- Taxonomy APIs use throttle rate set in ``DEFAULT_THROTTLE_RATES`` settings by default. Custom Throttle rate can by set by adding ``ScopedRateThrottle`` class in ``DEFAULT_THROTTLE_CLASSES`` settings and ``taxonomy-api-throttle-scope`` key in ``DEFAULT_THROTTLE_RATES``
- For the skill tags to be verified, the management command ``finalize_xblockskill_tags`` needs to be run periodically.
- Also, You can configure the skill tags verification by setting the values of ``MIN_VOTES_FOR_SKILLS`` and ``RATIO_THRESHOLD_FOR_SKILLS`` in the host platform or by passing the values to the command using the args ``--min-votes`` and ``--ratio-threshold``.


.. code-block:: python

    REST_FRAMEWORK = {
        'DEFAULT_THROTTLE_CLASSES': (
            'rest_framework.throttling.UserRateThrottle',
            'rest_framework.throttling.ScopedRateThrottle'
        ),
        'DEFAULT_THROTTLE_RATES': {
            'user': '100/hour',
            'taxonomy-api-throttle-scope': '60/min',  # custom throttle rate for taxonomy api
        },
    }


Developer Notes
~~~~~~~~~~~~~~~

- To run unit tests, create a virtualenv, install the requirements with ``make requirements`` and then run ``make test``
- To update the requirements, run ``make upgrade``
- To run quality checks, run ``make quality``
- Please do not import models directly in course discovery. e:g if you want to import CourseSkills in Discovery, use the utility get_whitelisted_course_skills instead of directly importing it.


Reporting Security Issues
-------------------------

Please do not report security issues in public. Please email security@edx.org.

Getting Help
------------

Have a question about this repository, or about Open edX in general?  Please
refer to this `list of resources`_ if you need any assistance.

.. _list of resources: https://open.edx.org/getting-help
