Change Log
==========

..
   All enhancements and patches to edx-enterprise will be documented
   in this file.  It adheres to the structure of http://keepachangelog.com/ ,
   but in reStructuredText instead of Markdown (for ease of incorporation into
   Sphinx documentation and the PyPI description).

   This project adheres to Semantic Versioning (http://semver.org/).

.. There should always be an "Unreleased" section for changes pending release.

Unreleased
--------------------

[1.3.2] - 2021-01-25
--------------------

* Added logs for signals and tasks.

[1.3.1] - 2021-01-22
--------------------

* Added the ability to black list course skills.

[1.3.0] - 2021-01-13
--------------------

* Added JobSkills.skill column and removed JobSkills.name column.

[1.2.1] - 2021-01-07
--------------------

* Added course update signal and handler to trigger the celery task
* Added celery task to update course skills
* Refactored `refresh_course_skills` management command

[1.2.0] - 2020-12-24
--------------------

* Fixed TypeError that pops up sometimes while communicating with the EMSI API.

[1.1.6] - 2020-12-24
--------------------

* Updated the README description.

[1.1.5] - 2020-12-18
--------------------

* Fixed travis issue related to PyPI upload.

[1.1.4] - 2020-12-17
--------------------

* Fixed the bug where EMSI API was returning 404 for job posting data.

[1.1.3] - 2020-11-05
--------------------

* Updating travis configuration.

[1.1.2] - 2020-10-20
--------------------

* Updating jobs-salary data's query.

[1.1.1] - 2020-10-20
--------------------

* Updating skills-jobs data's query.

[1.1.0] - 2020-09-30
--------------------

* Renamed main package name from taxonomy-service to taxonomy-connector.

[1.0.1] - 2020-09-21
--------------------

* Added package data, so that migrations and python packages are included in the final build.

[1.0.0] - 2020-09-09
--------------------

* Added Providers and Validators for integrations and upgraded to the first stable release.

[0.1.1] - 2020-09-09
--------------------

* Enable Travis integration

[0.1.0] - 2020-08-27
--------------------

* Added Basic skeleton and clients to call EMSI endpoint.
