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
[1.15.3] - 2022-03-11
---------------------

* fix: Check the course description length after encoding

[1.15.2] - 2022-02-18
---------------------

* feat: Added Support for large size course description translation

[1.15.1] - 2022-02-17
---------------------

* fix: Made the median_posting_duration in JobPosting Nullable to avoid errors on jenkins.

[1.15.0] - 2022-02-11
---------------------

* chore: Removed Django22, 30 and 31 support and added support for Django40

[1.14.5] - 2022-02-08
---------------------

* feat: Added Support for course description translation

[1.14.4] - 2022-01-28
---------------------

* feat: Add Translation model

[1.14.3] - 2021-10-27
---------------------

* fix: Make job names unique and handle exception where ever job is created/updated

[1.14.2] - 2021-09-08
---------------------

* Fixed an issue that was causing an error while index jobs data to algolia.

[1.14.1] - 2021-08-20
---------------------

* Decreased skills query chunk_size from 2000 to 50 to fetch more jobs.

[1.14.0] - 2021-08-16
---------------------

* Added managment command and related code to index jobs data to algolia.

[1.13.0] - 2021-08-9
---------------------

* Added Skill, Job and JobPostings viewsets.

[1.12.2] - 2021-08-5
---------------------

* Add job posting information in utility method `get_course_jobs`.

[1.12.1] - 2021-08-3
---------------------

* Add utility method `get_course_jobs` to return job associated with a course.

[1.12.0] - 2021-07-13
---------------------

* Added support for django 3.1 and 3.2

[1.11.2] - 2021-05-28
---------------------

* Added utility method to return serialized course skills.

[1.11.1] - 2021-04-20
---------------------

* Fixed .rst issues in CHANGELOG.rst

[1.11.0] - 2021-04-16
---------------------

* Mention currency in median salary field and add verbose name for models.

[1.10.0] - 2021-04-12
---------------------

* Remove all the usages of old `course_id` field including the column definition in `CourseSkills` model.

[1.9.0] - 2021-04-12
--------------------

* Replace the usages of old `course_id` in `CourseSkills` with the new `course_key` field.

[1.8.0] - 2021-04-09
--------------------

* Added a new field named `course_key` in `CourseSkills` model to deprecate and replace the old `course_id` field in future.

[1.7.0] - 2021-04-07
--------------------

* Removed RefreshCourseSkill view.

[1.6.2] - 2021-03-12
--------------------

* Handled edge cases in `refresh_course_skills` command.

[1.6.1] - 2021-03-10
--------------------

* Updated logging structure for `refresh_course_skills` command.

[1.6.0] - 2021-03-09
--------------------

* Added support for --all param in `refresh_course_skills` command to back populate data.

[1.5.0] - 2021-03-04
--------------------

* Added `populate_job_names` command.

[1.4.1] - 2021-02-19
--------------------

*  Added description field in Skill model and update the refresh_course_skill command to save skill description.
*  Pinning EMSI skills API version to 7.35

[1.4.0] - 2021-02-17
--------------------

* Updated refresh_job_skill command to get jobs related only to skills that are in our system
* Updated refresh_job_postings command to get job_posting only related to job we already have in our system.
* Added constrains on the Job, Skill, JobPostings, CourseSkill and JobSkill table.
* Added migration to remove all previous taxonomy data.
* Added utility to chuck the queryset provided.

[1.3.6] - 2021-01-29
--------------------

* Remove caching from EMSI API client.

[1.3.5] - 2021-01-27
--------------------

* Added some utility functions for adding/removing course skills to/from blacklist.

[1.3.4] - 2021-01-27
--------------------

* More logging.

[1.3.3] - 2021-01-26
--------------------

* Improve logging.

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
