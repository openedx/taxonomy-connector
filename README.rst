Taxonomy
========

.. image:: https://img.shields.io/pypi/v/taxonomy-connector.svg
    :target: https://pypi.org/project/taxonomy-connector/
    :alt: PyPI

.. image:: http://codecov.io/github/edx/taxonomy-connector/coverage.svg?branch=master
    :target: http://codecov.io/github/edx/taxonomy-connector?branch=master
    :alt: Codecov

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


Note:
In order to communicate with EMSI service, you need to set the values of ``client_id`` and ``client_secret``. These values are picked up from the host environment so you need to pass them in ``.yaml`` file of the host environment.


Also, to make taxonomy work, the host platform must add an implementation of data providers written in ``./taxonomy/providers``


Developer Notes
~~~~~~~~~~~~~~~

- To run unit tests, create a virtualenv, install the requirements with ``make requirements`` and then run ``make test``
- To update the requirements, run ``make upgrade``
- To run quality checks, run ``make quality``


Reporting Security Issues
-------------------------

Please do not report security issues in public. Please email security@edx.org.

Getting Help
------------

Have a question about this repository, or about Open edX in general?  Please
refer to this `list of resources`_ if you need any assistance.

.. _list of resources: https://open.edx.org/getting-help
