"""
Utils for taxonomy.
"""
import logging

from taxonomy.emsi_client import EMSISkillsApiClient
from taxonomy.exceptions import CourseMetadataNotFoundError, CourseSkillsRefreshError, TaxonomyAPIError
from taxonomy.models import BlacklistedCourseSkill, CourseSkills, Skill
from taxonomy.providers.utils import get_course_metadata_provider

LOGGER = logging.getLogger(__name__)


def update_skills_data(course_key, confidence, skill_data):
    """
    Persist the skills data in the database.
    """
    skill, __ = Skill.objects.update_or_create(**skill_data)

    if not is_course_skill_black_listed(course_key, skill.id):
        CourseSkills.objects.update_or_create(
            course_id=course_key,
            skill=skill,
            confidence=confidence
        )


def process_skills_data(course, course_skills, should_commit_to_db):
    """
    Process skills data returned by the EMSI service and update databased.

    Arguments:
        course (dict): Dictionary containing course data whose skills are being processed.
        course_skills (dict): Course skills data returned by the EMSI API.
        should_commit_to_db (bool): Boolean indicating whether data should be committed to database.
    """
    failures = set()

    for record in course_skills['data']:
        try:
            confidence = float(record['confidence'])
            skill = record['skill']
            skill_data = {
                'external_id': skill['id'],
                'name': skill['name'],
                'info_url': skill['infoUrl'],
                'type_id': skill['type']['id'],
                'type_name': skill['type']['name'],
            }
            if should_commit_to_db:
                update_skills_data(course['key'], confidence, skill_data)
        except KeyError:
            LOGGER.error('Missing keys in skills data for course_key: %s', course['key'])
            failures.add((course['uuid'], course['key']))
        except (ValueError, TypeError):
            LOGGER.error(
                'Invalid type for `confidence` in course skills for course_key: %s', course['key']
            )
            failures.add((course['uuid'], course['key']))

    return failures


def refresh_course_skills(options):
    """
    Refresh the skills associated with the provided courses.
    """
    courses = get_course_metadata_provider().get_courses(course_ids=options['course'])

    if not courses:
        raise CourseMetadataNotFoundError(
            'No course metadata was found for following courses. {}'.format(options['course'])
        )

    failures = set()
    client = EMSISkillsApiClient()
    for course in courses:
        course_description = course['full_description']

        if course_description:
            try:
                course_skills = client.get_course_skills(course_description)
            except TaxonomyAPIError:
                LOGGER.error('Taxonomy API Error for course_key: %s', course['key'])
                failures.add((course['uuid'], course['key']))
            else:
                failed_records = process_skills_data(course, course_skills, options['commit'])
                failures.update(failed_records)

    if failures:
        keys = sorted('{key} ({uuid})'.format(key=course_key, uuid=uuid) for uuid, course_key in failures)
        raise CourseSkillsRefreshError(
            'Could not refresh skills for the following courses: {course_keys}'.format(
                course_keys=', '.join(keys)
            )
        )


def black_list_course_skill(course_key, skill_id):
    """
    Blacklist a course skill.

    Arguments:
        course_key (CourseKey): CourseKey object pointing to the course whose skill need to be black-listed.
        skill_id (int): Primary key identifier of the skill that need to be blacklisted.

    Returns:
        (BlacklistedCourseSkill): Newly created instance of the BlacklistedCourseSkill.
    """
    black_listed_course_skill, __ = BlacklistedCourseSkill.objects.get_or_create(
        course_id=course_key,
        skill_id=skill_id,
    )
    return black_listed_course_skill


def is_course_skill_black_listed(course_key, skill_id):
    """
    Return the black listed status of a course skill.

    Arguments:
        course_key (CourseKey): CourseKey object pointing to the course whose skill need to be checked.
        skill_id (int): Primary key identifier of the skill that need to be checked.

    Returns:
        (bool): True if course-skill (identified by the arguments) is black-listed, False otherwise.
    """
    return BlacklistedCourseSkill.objects.filter(
        course_id=course_key,
        skill_id=skill_id
    ).exists()
