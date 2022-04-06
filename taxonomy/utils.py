"""
Utils for taxonomy.
"""
import logging
import time
import boto3

from bs4 import BeautifulSoup
from taxonomy.constants import (
    AMAZON_TRANSLATION_ALLOWED_SIZE,
    AUTO,
    ENGLISH,
    REGION,
    TRANSLATE_SERVICE,
    EMSI_API_RATE_LIMIT_PER_SEC
)
from taxonomy.emsi_client import EMSISkillsApiClient
from taxonomy.exceptions import TaxonomyAPIError
from taxonomy.models import CourseSkills, JobSkills, Skill, Translation
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
    for index, course in enumerate(courses, start=1):
        course_description = course['full_description']
        if course_description:
            course_translated_description = get_translated_course_description(course['key'], course_description)
            try:
                # EMSI only allows 5 requests/sec
                # We need to add one sec delay after every 5 requests to prevent 429 errors
                if index % EMSI_API_RATE_LIMIT_PER_SEC == 0:
                    time.sleep(1)  # sleep for 1 second
                course_skills = client.get_course_skills(course_translated_description)
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


def get_translated_course_description(course_key, course_description):
    """
    Return translated course description.

    Create translation for course description if translation object doesn't already exist.
     OR update translation if course description changed from previous description in translation and
      return the translated course description.

    Arguments:
        course_key (str): Key of the course whose description needs to be translated.
        course_description (str): Full course description of the course which needs to be translated.

    Returns:
        str: Translated full course description.
    """
    translation = Translation.objects.filter(
        source_model_name='Course',
        source_model_field='full_description',
        source_record_identifier=course_key
    ).first()
    if translation:
        if translation.source_text != course_description:
            if (len(course_description.encode('utf-8'))) < AMAZON_TRANSLATION_ALLOWED_SIZE:
                result = translate_text(course_key, course_description, AUTO, ENGLISH)
            else:
                result = apply_batching_to_translate_large_text(course_key, course_description)
            if not result['TranslatedText']:
                return course_description
            if result['SourceLanguageCode'] == ENGLISH:
                translation.translated_text = course_description
            else:
                translation.translated_text = result['TranslatedText']
            LOGGER.info(f'[TAXONOMY] Translate course description updated for key: {course_key}')
            translation.source_text = course_description
            translation.source_language = result['SourceLanguageCode']
            translation.save()
        return translation.translated_text
    if (len(course_description.encode('utf-8'))) < AMAZON_TRANSLATION_ALLOWED_SIZE:
        result = translate_text(course_key, course_description, AUTO, ENGLISH)
    else:
        result = apply_batching_to_translate_large_text(course_key, course_description)
    if not result['TranslatedText']:
        return course_description
    if result['SourceLanguageCode'] == ENGLISH:
        translated_text = course_description
    else:
        translated_text = result['TranslatedText']

    translation = Translation.objects.create(
        source_model_name='Course',
        source_model_field='full_description',
        source_record_identifier=course_key,
        source_text=course_description,
        translated_text=translated_text,
        translated_text_language=ENGLISH,
        source_language=result['SourceLanguageCode'],
    )
    LOGGER.info(f'[TAXONOMY] Translate course description created for key: {course_key}')
    return translation.translated_text


def translate_text(key, text, source_language, target_language):
    """
    Translate text into the target language.

    Arguments:
        key (str): Key or id of the object to uniquely identify.
        text (str): Text which needs to be translated.
        source_language (str): Source Language of text if known otherwise provide auto.
        target_language (str): Desired language in which text needs to be converted.

    Returns:
        dict: Translated object which contains TranslatedText, SourceLanguageCode and TargetLanguageCode.
    """
    translate = boto3.client(service_name=TRANSLATE_SERVICE, region_name=REGION)

    result = {'SourceLanguageCode': '', 'TranslatedText': ''}
    try:
        result = translate.translate_text(
            Text=text,
            SourceLanguageCode=source_language,
            TargetLanguageCode=target_language,
        )
    except Exception as ex:  # pylint: disable=broad-except
        message = f'[TAXONOMY] Translate course description exception for key: {key} Error: {ex}'
        LOGGER.exception(message)

    return result


def apply_batching_to_translate_large_text(course_key, source_text):
    """
    Apply batching if text to translate is large and then combine it again.

    Arguments:
        course_key (str): Key or id of the object to uniquely identify.
        source_text (str): Text which needs to be translated.

    Returns:
        dict: Translated object which contains TranslatedText and SourceLanguageCode.
    """
    soup = BeautifulSoup(source_text, 'html.parser')
    # Split input text into a list of sentences on the basis of html tags
    sentences = soup.findAll()
    translated_text = ''
    source_text_chunk = ''
    result = {}
    source_language_code = ''
    LOGGER.info(f'[TAXONOMY] Translate course description applying batching for key: {course_key}')

    for sentence in sentences:
        # Translate expects utf-8 encoded input to be no more than
        # 5000 bytes, so we’ll split on the 5000th byte.

        if len(sentence.encode('utf-8')) + len(source_text_chunk.encode('utf-8')) < AMAZON_TRANSLATION_ALLOWED_SIZE:
            source_text_chunk = '%s%s' % (source_text_chunk, sentence)
        else:
            translation_chunk = translate_text(course_key, source_text_chunk, AUTO, ENGLISH)
            translated_text = translated_text + translation_chunk['TranslatedText']
            source_text_chunk = sentence
            source_language_code = translation_chunk['SourceLanguageCode']

    # Translate the final chunk of input text
    if source_text_chunk:
        translation_chunk = translate_text(course_key, source_text_chunk, AUTO, ENGLISH)
        translated_text = translated_text + translation_chunk['TranslatedText']
        source_language_code = translation_chunk['SourceLanguageCode']
    # bs4 adds /r/n which needs to be removed for consistency.
    translated_text = translated_text.replace('\r', '').replace('\n', '')
    result['TranslatedText'] = translated_text
    result['SourceLanguageCode'] = source_language_code
    return result
