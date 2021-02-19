"""
Utils for taxonomy.
"""
import logging

from taxonomy.emsi_client import EMSISkillsApiClient
from taxonomy.exceptions import CourseMetadataNotFoundError, CourseSkillsRefreshError, TaxonomyAPIError
from taxonomy.models import CourseSkills, Skill
from taxonomy.providers.utils import get_course_metadata_provider

LOGGER = logging.getLogger(__name__)


def update_skills_data(course_key, skill_external_id, confidence, skill_data):
    """
    Persist the skills data in the database.
    """
    skill, __ = Skill.objects.update_or_create(external_id=skill_external_id, defaults=skill_data)

    if not is_course_skill_blacklisted(course_key, skill.id):
        CourseSkills.objects.update_or_create(
            course_id=course_key,
            skill=skill,
            defaults={
                'confidence': confidence
            },
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
            skill_external_id = skill['id']
            skill_data = {
                'name': skill['name'],
                'info_url': skill['infoUrl'],
                'type_id': skill['type']['id'],
                'type_name': skill['type']['name'],
                'description': skill['description']
            }
            if should_commit_to_db:
                update_skills_data(course['key'], skill_external_id, confidence, skill_data)
        except KeyError:
            LOGGER.error('[TAXONOMY] Missing keys in skills data for course_key: %s', course['key'])
            failures.add((course['uuid'], course['key']))
        except (ValueError, TypeError):
            LOGGER.error(
                '[TAXONOMY] Invalid type for `confidence` in course skills for course_key: %s', course['key']
            )
            failures.add((course['uuid'], course['key']))

    return failures


def refresh_course_skills(options):
    """
    Refresh the skills associated with the provided courses.
    """
    LOGGER.info('[TAXONOMY] Refresh Course Skills. Options: [%s]', options)

    courses = get_course_metadata_provider().get_courses(course_ids=options['course'])

    if not courses:
        raise CourseMetadataNotFoundError(
            'No course metadata was found for following courses. {}'.format(options['course'])
        )

    LOGGER.info('[TAXONOMY] Courses Information. Data: [%s]', courses)

    failures = set()
    client = EMSISkillsApiClient()
    for course in courses:
        course_description = course['full_description']

        if course_description:
            try:
                course_skills = client.get_course_skills(course_description)
                LOGGER.info('[TAXONOMY] Skills data recived from EMSI. Skills: [%s]', course_skills)
            except TaxonomyAPIError:
                LOGGER.error('[TAXONOMY] API Error for course_key: %s', course['key'])
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


def blacklist_course_skill(course_key, skill_id):
    """
    Blacklist a course skill.

    Arguments:
        course_key (CourseKey): CourseKey object pointing to the course whose skill need to be black-listed.
        skill_id (int): Primary key identifier of the skill that need to be blacklisted.
    """
    CourseSkills.objects.filter(
        course_id=course_key,
        skill_id=skill_id,
    ).update(is_blacklisted=True)


def remove_course_skill_from_blacklist(course_key, skill_id):
    """
    Remove a course skill from the blacklist.

    Arguments:
        course_key (CourseKey): CourseKey object pointing to the course whose skill need to be black-listed.
        skill_id (int): Primary key identifier of the skill that need to be blacklisted.
    """
    CourseSkills.objects.filter(
        course_id=course_key,
        skill_id=skill_id,
    ).update(is_blacklisted=False)


def is_course_skill_blacklisted(course_key, skill_id):
    """
    Return the black listed status of a course skill.

    Arguments:
        course_key (CourseKey): CourseKey object pointing to the course whose skill need to be checked.
        skill_id (int): Primary key identifier of the skill that need to be checked.

    Returns:
        (bool): True if course-skill (identified by the arguments) is black-listed, False otherwise.
    """
    return CourseSkills.objects.filter(
        course_id=course_key,
        skill_id=skill_id,
        is_blacklisted=True,
    ).exists()


def get_whitelisted_course_skills(course_key, prefetch_skills=True):
    """
    Get all the course skills that are not blacklisted.

    Arguments:
        course_key (str): Key of the course whose course skills need to be returned.
        prefetch_skills (bool): If True, Prefetch related skills in a single query using Django's select_related.

    Returns:
        (list<CourseSkills>): A list of all the course skills that are not blacklisted.
    """
    qs = CourseSkills.objects.filter(course_id=course_key, is_blacklisted=False)
    if prefetch_skills:
        qs = qs.select_related('skill')
    return qs.all()


def get_blacklisted_course_skills(course_key, prefetch_skills=True):
    """
    Get all the blacklisted course skills.

    Arguments:
        course_key (str): Key of the course whose course skills need to be returned.
        prefetch_skills (bool): If True, Prefetch related skills in a single query using Django's select_related.

    Returns:
        (list<CourseSkills>): A list of all the course skills that are blacklisted.
    """
    qs = CourseSkills.objects.filter(course_id=course_key, is_blacklisted=True)
    if prefetch_skills:
        qs = qs.select_related('skill')
    return qs.all()


def chunked_queryset(queryset, chunk_size=100):
    """
    Slice a queryset into chunks.
    """
    start_pk = 0
    queryset = queryset.order_by('pk')

    while True:
        # No entry left
        if not queryset.filter(pk__gt=start_pk).exists():
            return

        try:
            # Fetch chunk_size entries if possible
            end_pk = queryset.filter(pk__gt=start_pk).values_list('pk', flat=True)[chunk_size - 1]

            # Fetch rest entries if less than chunk_size left
        except IndexError:
            end_pk = queryset.values_list('pk', flat=True).last()

        yield queryset.filter(pk__gt=start_pk).filter(pk__lte=end_pk)

        start_pk = end_pk
