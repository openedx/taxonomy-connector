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

[1.39.0] - 2023-05-09
---------------------
* feat: Added CourseRunMetadataProvider to fetch course run info.
* feat: Added CourseRunXBlockSkillsTracker model to track xblock tagging under courses.
* Switch from ``edx-sphinx-theme`` to ``sphinx-book-theme`` since the former is
  deprecated.  See https://github.com/openedx/edx-sphinx-theme/issues/184 for
  more details.

[1.38.1] - 2023-05-11
---------------------
* fix: Update the `attributesForFaceting` list to include the `b2c_opt_in` field

[1.38.0] - 2023-05-03
---------------------
* feat: Added a new attribute (`b2c_opt_in`) to the JobSerializer

[1.37.3] - 2023-05-03
---------------------
* feat: generate job description only if job has name and description is empty

[1.37.2] - 2023-04-27
---------------------
* feat: Generate ai based job descriptions

[1.37.1] - 2023-03-31
---------------------
* feat: making sub_category skills to job specific in career tab.

[1.37.0] - 2023-03-31
---------------------
* Added the ability to remove unused jobs from django admin.

[1.36.3] - 2023-03-29
---------------------
* fix: Do not create a job if all of the releated skills does not exist in database

[1.36.2] - 2023-03-08
---------------------
* fix: remove validations on skills in skill quiz

[1.36.1] - 2023-02-23
---------------------
* Index industry data with skills in Algolia.

[1.36.0] - 2023-02-20
---------------------
* Added handler for openedx-events: XBLOCK_SKILL_VERIFIED.

[1.35.1] - 2023-02-10
---------------------
* Enabled ordering in SkillsQuizViewSet.

[1.35.0] - 2023-02-07
---------------------
* Added logic to avoid 429 errors and handle these errors if they still appear while communicating with LightCast API.

[1.34.0] - 2023-01-10
---------------------
* Added similar jobs list in jobs algolia jobs index.

[1.33.0] - 2023-01-09
---------------------
* https://github.com/openedx/openedx-events/pull/143 merged, so adding back
  changes reverted in version 1.32.1
* Added refresh_xblock_skills command to update skills for xblocks.
* Added handlers for openedx-events: XBLOCK_DELETED, XBLOCK_PUBLISHED and XBLOCK_PUBLISHED.
* Added finalize_xblockskill_tags to mark skills as verified or blacklisted.

[1.32.3] - 2023-01-05
---------------------
* Added log for EMSI client access token and raising error for error status.

[1.32.2] - 2023-01-02
---------------------
* updated requirements.

[1.32.1] - 2022-12-20
---------------------
* Reverts changes depending on openedx-events till upstream MR is merged.
  https://github.com/openedx/openedx-events/pull/143

[1.32.0] - 2022-12-20
---------------------
* Added refresh_xblock_skills command to update skills for xblocks.

[1.31.2] - 2022-12-23
---------------------
* Added ACCESS_TOKEN_EXPIRY_THRESHOLD_IN_SECONDS in EMSI client.

[1.31.1] - 2022-12-19
---------------------
* Handle repeating industry names in algolia index and test

[1.31.0] - 2022-12-06
---------------------
* Added handlers for openedx-events: XBLOCK_DELETED, XBLOCK_PUBLISHED and XBLOCK_PUBLISHED.

[1.30.1] - 2022-12-06
---------------------
* Added xblocks to skill API.
* Added xblocks API.

[1.30.0] - 2022-12-06
---------------------
* Added industry_names facet in Algolia Jobs Index.

[1.29.0] - 2022-11-28
---------------------
* Added XBlockSkills and XBlockSkillData models.
* Added related celery tasks, abstract provider, signals and commands.
* Added management command to verify xblockskill tags.

[1.28.2] - 2022-11-23
---------------------
* Added industry_names field in Algolia serializer.

[1.28.1] - 2022-11-22
---------------------
* Added JobHolderUsernamesAPIView which returns a list of 100 usernames from SkillsQuiz.

[1.28.0] - 2022-11-21
---------------------
* Updated refresh_job_skills command to save industry relation with job and skills.

[1.27.0] - 2022-10-31
---------------------
* Removed industry foreign key from JobSkills table and create a new table IndustryJobSkill.

[1.26.0] - 2022-10-31
---------------------
* Added relation between JobSkill and Industry Table.

[1.25.0] - 2022-10-24
---------------------
* Added JobTopSkillCategoriesAPIView.

[1.24.0] - 2022-10-21
---------------------
* Added a new model to store industry data using NAICS2 codes.

[1.23.1] - 2022-10-13
---------------------
* Do no concatenate if `short_description is `None`.
* Fix CourseSkills update_or_create call.

[1.23.0] - 2022-10-05
---------------------
* Expand course skills tagging to include `title`, `short_description` and `full_description`.

[1.22.5] - 2022-09-16
---------------------
* Fixes product type issue by using ProductTypes choices.

[1.22.4] - 2022-09-14
---------------------
* Updated utils to support program skills.

[1.22.3] - 2022-09-07
---------------------
* Added support to filter Skills by names.

[1.22.2] - 2022-09-06
---------------------
* Register Program associated models on Admin.
* Change verbose name for RefreshProgramSkillsConfig model

[1.22.1] - 2022-08-26
---------------------
* Added id field in JobSerializer for Algolia.

[1.22.0] - 2022-08-22
---------------------
* Added a new model for storing user response for skills quiz.
* Added new REST endpoints for performing CRUD operations on skills quiz.

[1.21.0] - 2022-08-16
---------------------
* feat: add task to update program skills through EMSI api

[1.20.0] - 2022-08-11
---------------------
* feat: add caching to ``utils.get_whitelisted_serialized_skills()``

[1.19.0] - 2022-08-04
---------------------
* feat: add provider and validator for Programs

[1.18.0] - 2022-08-01
---------------------
* feat: add program skill model
* feat: Update SkillSerializer to include Category and Subcategory details.

[1.17.1] - 2022-07-29
---------------------

* feat: use program update signal to call EMSI API

[1.17.0] - 2022-07-15
---------------------

* refactor: Remove EdxRestApiClient usage in taxonomy-connector

[1.16.3] - 2022-06-23
---------------------

* Added handling for None values for median salary from EMSI.

[1.16.2] - 2022-06-22
---------------------

* Fixed error causes by null values returned by EMSI API.

[1.16.1] - 2022-06-15
---------------------

* Fixed API 429 error and updated admin list display for skills for better usability.

[1.16.0] - 2022-06-08
---------------------

* Added category and subcategory for skill.

[1.15.4] - 2022-04-06
---------------------

* fix: Add limit to EMSI API calls

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
