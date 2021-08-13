"""
Utils for taxonomy.
"""
import logging

from taxonomy.emsi_client import EMSISkillsApiClient
from taxonomy.exceptions import TaxonomyAPIError
from taxonomy.models import CourseSkills, JobSkills, Skill
from taxonomy.serializers import SkillSerializer

LOGGER = logging.getLogger(__name__)


def get_whitelisted_serialized_skills(course_key):
    """
    Get a list of serialized course skills.

    Arguments:
        course_key (str): Key of the course whose course skills need to be returned.

    Returns:
        (dict): A dictionary containing the following key-value pairs
            1.  name: 'Skill name'
            2. description: "Skill Description"
    """
    course_skills = get_whitelisted_course_skills(course_key)
    skills = [course_skill.skill for course_skill in course_skills]
    serializer = SkillSerializer(skills, many=True)
    return serializer.data


def update_skills_data(course_key, skill_external_id, confidence, skill_data):
    """
    Persist the skills data in the database.
    """
    skill, __ = Skill.objects.update_or_create(external_id=skill_external_id, defaults=skill_data)

    if not is_course_skill_blacklisted(course_key, skill.id):
        CourseSkills.objects.update_or_create(
            course_key=course_key,
            skill=skill,
            defaults={
                'confidence': confidence,
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
    failures = []
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
            message = f'[TAXONOMY] Missing keys in skills data for course_key: {course["key"]}'
            LOGGER.error(message)
            failures.append((course['uuid'], message))
        except (ValueError, TypeError):
            message = f'[TAXONOMY] Invalid type for `confidence` in course skills for course_key: {course["key"]}'
            LOGGER.error(message)
            failures.append((course['uuid'], message))
    return failures


def refresh_course_skills(courses, should_commit_to_db):
    """
    Refresh the skills associated with the provided courses.
    """
    all_failures = []
    success_courses_count = 0
    skipped_courses_count = 0

    client = EMSISkillsApiClient()

    for course in courses:
        course_description = course['full_description']
        if course_description:
            try:
                course_skills = client.get_course_skills(course_description)
            except TaxonomyAPIError:
                message = f'[TAXONOMY] API Error for course_key: {course["key"]}'
                LOGGER.error(message)
                all_failures.append((course['uuid'], message))
                continue

            try:
                failures = process_skills_data(course, course_skills, should_commit_to_db)
                if failures:
                    LOGGER.info('[TAXONOMY] Skills data received from EMSI. Skills: [%s]', course_skills)
                    all_failures += failures
                else:
                    success_courses_count += 1
            except Exception as ex:  # pylint: disable=broad-except
                LOGGER.info('[TAXONOMY] Skills data received from EMSI. Skills: [%s]', course_skills)
                message = f'[TAXONOMY] Exception for course_key: {course["key"]} Error: {ex}'
                LOGGER.error(message)
                all_failures.append((course['uuid'], message))
        else:
            skipped_courses_count += 1

    LOGGER.info(
        '[TAXONOMY] Refresh course skills process completed. \n'
        'Failures: %s \n'
        'Total Courses Updated Successfully: %s \n'
        'Total Courses Skipped: %s \n'
        'Total Failures: %s \n',
        all_failures,
        success_courses_count,
        skipped_courses_count,
        len(all_failures),
    )


def blacklist_course_skill(course_key, skill_id):
    """
    Blacklist a course skill.

    Arguments:
        course_key (CourseKey): CourseKey object pointing to the course whose skill need to be black-listed.
        skill_id (int): Primary key identifier of the skill that need to be blacklisted.
    """
    CourseSkills.objects.filter(
        course_key=course_key,
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
        course_key=course_key,
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
        course_key=course_key,
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
    qs = CourseSkills.objects.filter(course_key=course_key, is_blacklisted=False)
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
    qs = CourseSkills.objects.filter(course_key=course_key, is_blacklisted=True)
    if prefetch_skills:
        qs = qs.select_related('skill')
    return qs.all()


def get_course_jobs(course_key):
    """
    Get data for all course jobs.

    Arguments:
        course_key (str): Key of the course whose course skills need to be returned.

    Returns:
        list: A list of dicts where each dict contain information about a particular job.
    """
    course_skills = get_whitelisted_course_skills(course_key)
    job_skills = JobSkills.objects.select_related(
        'skill',
        'job',
        'job__jobpostings',
    ).filter(
        skill__in=[course_skill.skill for course_skill in course_skills]
    )
    data = []
    for job_skill in job_skills:
        job_posting = job_skill.job.jobpostings_set.first()
        data.append(
            {
                'name': job_skill.job.name,
                'median_salary': job_posting.median_salary,
                'unique_postings': job_posting.unique_postings,
            }
        )
    return data
