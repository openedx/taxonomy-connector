"""
Utils for taxonomy.
"""
import logging
import time
from typing import Union
import boto3

from bs4 import BeautifulSoup
from django.utils.timezone import now
from edx_django_utils.cache import get_cache_key, TieredCache
from edx_django_utils.cache.utils import hashlib

from taxonomy.choices import ProductTypes
from taxonomy.constants import (
    AMAZON_TRANSLATION_ALLOWED_SIZE,
    AUTO,
    ENGLISH,
    REGION,
    TRANSLATE_SERVICE,
    EMSI_API_RATE_LIMIT_PER_SEC
)
from taxonomy.emsi.client import EMSISkillsApiClient
from taxonomy.exceptions import TaxonomyAPIError
from taxonomy.models import CourseSkills, ProgramSkill, JobSkills, Skill, Translation, XBlockSkillData, XBlockSkills
from taxonomy.serializers import SkillSerializer

LOGGER = logging.getLogger(__name__)
CACHE_TIMEOUT_COURSE_SKILLS_SECONDS = 60 * 60

COURSE_METADATA_FIELDS_COMBINED = 'title:short_description:full_description'


def get_whitelisted_serialized_skills(key_or_uuid, product_type=ProductTypes.Course):
    """
    Get a list of serialized course skills.

    Arguments:
        key_or_uuid (str): Key or uuid of the product whose skills need to be returned.
        product_type (str): String indicating about the product type.

    Returns:
        (dict): A dictionary containing the following key-value pairs
            1.  name: 'Skill name'
            2. description: "Skill Description"
    """
    subdomain, identifier = \
        ('course_skills', 'course_key') if product_type == ProductTypes.Course else ('program_skills', 'program_uuid')
    kwargs = {
        'domain': 'taxonomy',
        'subdomain': subdomain,
        identifier: key_or_uuid
    }
    cache_key = get_cache_key(**kwargs)
    cached_response = TieredCache.get_cached_response(cache_key)
    if cached_response.is_found:
        return cached_response.value

    product_skills = get_whitelisted_product_skills(key_or_uuid, product_type)
    skills = [product_skill.skill for product_skill in product_skills]
    skills_data = SkillSerializer(skills, many=True).data
    TieredCache.set_all_tiers(
        cache_key,
        skills_data,
        django_cache_timeout=CACHE_TIMEOUT_COURSE_SKILLS_SECONDS,
    )
    return skills_data


def get_product_identifier(product_type):
    """
    Return the identifier of a Product Model from Discovery.
    """
    identifier = None
    if product_type == ProductTypes.Program:
        identifier = 'uuid'
    elif product_type in (ProductTypes.Course, ProductTypes.XBlock):
        identifier = 'key'

    return identifier


def get_product_skill_model_and_identifier(product_type):
    """
    Return the Skill Model along with its identifier based on product type.
    """
    product_skill = (CourseSkills, 'course_key')
    if product_type == ProductTypes.Program:
        product_skill = (ProgramSkill, 'program_uuid')
    elif product_type == ProductTypes.XBlock:
        product_skill = (XBlockSkills, 'usage_key')
    elif product_type == ProductTypes.XBlockData:
        product_skill = (XBlockSkillData, 'xblock_id')
    return product_skill


def _create_xblockskill_with_hash(key_or_uuid, hash_content):
    """
    Create or update a XBlockSkill object with hash of the text content.

    Args:
        key_or_uuid (str): product uuid
        hash_content (str): hash of content

    Returns:
        XBlockSkills object
    """
    model, identifier = get_product_skill_model_and_identifier(ProductTypes.XBlock)
    product, _ = model.objects.update_or_create(
        **{identifier: key_or_uuid},
        defaults={'hash_content': hash_content, 'auto_processed': True},
    )
    return product


def update_skills_data(key_or_uuid, skill_external_id, confidence, skill_data, product_type, **kwargs):
    """
    Persist the skills data in the database for Program, Course or XBlock.

    Args:
        key_or_uuid (str): key or uuid of the object whose skill is to be updated.
        skill_external_id (str): id from external api
        confidence (float): confidence from external api
        skill_data (dict): data from external api about the skill
        product_type (ProductTypes): type of product
        **kwargs: It should contain `hash_content` in case the product_type is XBlockSkills

    Returns:

    """
    skill, _ = Skill.objects.update_or_create(external_id=skill_external_id, defaults=skill_data)
    if product_type == ProductTypes.XBlock:
        xblock = _create_xblockskill_with_hash(key_or_uuid, kwargs.get('hash_content'))
        key_or_uuid = xblock.id
        product_type = ProductTypes.XBlockData
    if is_skill_blacklisted(key_or_uuid, skill.id, product_type):
        return
    skill_model, identifier = get_product_skill_model_and_identifier(product_type)
    condition = {identifier: key_or_uuid, 'skill': skill}
    defaults = {'confidence': confidence}
    _, created = skill_model.objects.update_or_create(**condition, defaults=defaults)
    action = 'created' if created else 'updated'
    LOGGER.info(f'{skill_model} {action} for key {key_or_uuid}')


def process_skills_data(product, skills, should_commit_to_db, product_type, **kwargs):
    """
    Process skills data returned by the EMSI service and update databased.

    Arguments:
        product (dict): Dictionary containing course or program data whose skills are being processed.
        skills (dict): Course or Program skills data returned by the EMSI API.
        should_commit_to_db (bool): Boolean indicating whether data should be committed to database.
        product_type (str): String indicating about the product type.
        **kwargs: It should contain `hash_content` in case the product_type is XBlockSkills
    """
    failures = []
    key_or_uuid = get_product_identifier(product_type)
    for record in skills['data']:
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
                update_skills_data(
                    product[key_or_uuid], skill_external_id, confidence, skill_data, product_type, **kwargs
                )
        except KeyError:
            message = f'[TAXONOMY] Missing keys in skills data for key: {product[key_or_uuid]}'
            LOGGER.error(message)
            failures.append((product['uuid'], message))
        except (ValueError, TypeError):
            message = f'[TAXONOMY] Invalid type for `confidence` in skills for key: {product[key_or_uuid]}'
            LOGGER.error(message)
            failures.append((product[key_or_uuid], message))
    return failures


def get_translation_attr(product_type):
    """
    Return properties based on product type.
    """
    translation_attr = COURSE_METADATA_FIELDS_COMBINED
    if product_type == ProductTypes.Program:
        translation_attr = 'overview'
    elif product_type == ProductTypes.XBlock:
        translation_attr = 'content'
    return translation_attr


def get_course_metadata_fields_text(course_attrs_string, course):
    """
    Extract, combine and return text for multiple metadata fields of a course.
    """
    course_attr_values = []
    for course_attr in course_attrs_string.split(':'):
        course_attr_values.append(course[course_attr])
    return ' '.join(filter(bool, course_attr_values)).strip()


def get_hash(text_data: str):
    """
    Return hash for given text_data.
    """
    processed_text = text_data.replace(" ", "").strip()
    if not processed_text:
        return None
    return hashlib.md5(processed_text.encode()).hexdigest()


def process_skill_attr_text(text_data: str, product_type: ProductTypes) -> dict:
    """
    Return metadata for text_data.
    """
    extra_data = {}
    if product_type == ProductTypes.XBlock:
        hash_content = get_hash(text_data)
        if hash_content:
            extra_data['hash_content'] = hash_content
    return extra_data


def skip_product_processing(extra_data: dict, key_or_uuid: str, product_type: ProductTypes) -> bool:
    """
    Check whether to skip processing.
    """
    # currently only xblock text is checked
    if product_type != ProductTypes.XBlock:
        return False

    if not extra_data:
        return True
    model, identifier = get_product_skill_model_and_identifier(product_type)
    skill_filter = {
        identifier: key_or_uuid,
        'auto_processed': True,
        **extra_data,
    }
    no_change = model.objects.filter(**skill_filter).exists()
    if no_change:
        # text with same hash exists, so skip further processing
        return True
    return False


def _convert_product_to_dict(product: Union[dict, tuple]):
    """
    Convert product data to dict.
    """
    product_dict = None
    if isinstance(product, dict):
        product_dict = product
    elif isinstance(product, tuple) and hasattr(product, '_asdict'):
        product_dict = product._asdict()
    return product_dict


def refresh_product_skills(products, should_commit_to_db, product_type):
    """
    Refresh the skills associated with the provided products.
    """
    all_failures = []
    success_count = 0
    skipped_count = 0
    skill_extraction_attr, key_or_uuid = get_translation_attr(product_type), get_product_identifier(product_type)

    client = EMSISkillsApiClient()

    for index, product in enumerate(products, start=1):
        product = _convert_product_to_dict(product)
        if product is None:
            skipped_count += 1
            continue
        if product_type == ProductTypes.Course:
            skill_attr_val = get_course_metadata_fields_text(skill_extraction_attr, product)
        else:
            skill_attr_val = product[skill_extraction_attr]
        if skill_attr_val:
            # get metadata of skill_attr_val
            extra_data = process_skill_attr_text(skill_attr_val, product_type)
            if skip_product_processing(extra_data, product[key_or_uuid], product_type):
                skipped_count += 1
                continue
            # TODO: Skip translation for xblock text till we find better way to
            # handle huge amounts of text
            if product_type == ProductTypes.XBlock:
                # TODO: make sure that skill_attr_val is in english
                translated_skill_attr = skill_attr_val
            else:
                translated_skill_attr = get_translated_skill_attribute_val(
                    product[key_or_uuid], skill_attr_val, product_type
                )
            try:
                # EMSI only allows 5 requests/sec
                # We need to add one sec delay after every 5 requests to prevent 429 errors
                if index % EMSI_API_RATE_LIMIT_PER_SEC == 0:
                    time.sleep(1)  # sleep for 1 second
                skills = client.get_product_skills(translated_skill_attr)
            except TaxonomyAPIError:
                message = f'[TAXONOMY] API Error for key: {product[key_or_uuid]}'
                LOGGER.error(message)
                all_failures.append((product['uuid'], message))
                continue

            try:
                failures = process_skills_data(
                    product,
                    skills,
                    should_commit_to_db,
                    product_type,
                    **extra_data
                )
                if failures:
                    LOGGER.info('[TAXONOMY] Skills data received from EMSI. Skills: [%s]', skills)
                    all_failures += failures
                else:
                    success_count += 1
            except Exception as ex:  # pylint: disable=broad-except
                LOGGER.info('[TAXONOMY] Skills data received from EMSI. Skills: [%s]', skills)
                message = f'[TAXONOMY] Exception for key: {product[key_or_uuid]} Error: {ex}'
                LOGGER.error(message)
                all_failures.append((product[key_or_uuid], message))
        else:
            skipped_count += 1

    LOGGER.info(
        '[TAXONOMY] Refresh %s skills process completed. \n'
        'Failures: %s \n'
        'Total %s Updated Successfully: %s \n'
        'Total %s Skipped: %s \n'
        'Total Failures: %s \n',
        product_type,
        all_failures,
        product_type,
        success_count,
        product_type,
        skipped_count,
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


def is_skill_blacklisted(key_or_uuid, skill_id, product_type):
    """
    Return the black listed status of a course or program skill.

    Arguments:
        key_or_uuid: CourseKey, UsageKey or ProgramUUID object whose skill need to be checked.
        skill_id (int): Primary key identifier of the skill that need to be checked.
        is_programs(bool): Boolean indicating which Skill Model would be selected.

    Returns:
        (bool): True if skill (identified by the arguments) is black-listed, False otherwise.
    """
    skill_model, identifier = get_product_skill_model_and_identifier(product_type)
    kwargs = {
        identifier: key_or_uuid,
        'skill_id': skill_id,
        'is_blacklisted': True
    }
    return skill_model.objects.filter(**kwargs).exists()


def get_whitelisted_product_skills(key_or_uuid, product_type=ProductTypes.Course, prefetch_skills=True):
    """
    Get all the product skills that are not blacklisted.

    Arguments:
        key_or_uuid (str): Key or uuid of the product whose skills need to be returned.
        product_type (str): String indicating about the product type.
        prefetch_skills (bool): If True, Prefetch related skills in a single query using Django's select_related.

    Returns:
        (list<CourseSkills/ProgramSkills>): A list of all the product skills that are not blacklisted.
    """
    skill_model, identifier = get_product_skill_model_and_identifier(product_type)
    kwargs = {
        identifier: key_or_uuid,
        'is_blacklisted': False
    }
    qs = skill_model.objects.filter(**kwargs)
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


def get_course_jobs(course_key, product_type=ProductTypes.Course):
    """
    Get data for all course jobs.

    Arguments:
        course_key (str): Key of the course whose course skills need to be returned.
        product_type (str): String indicating about the product type.

    Returns:
        list: A list of dicts where each dict contain information about a particular job.
    """
    course_skills = get_whitelisted_product_skills(course_key, product_type)
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


def get_translated_skill_attribute_val(key_or_uuid, skill_attr_val, product_type):
    """
    Return translated skill attribute value either for a course or a program.

    Create translation for provided skill attribute if translation object doesn't already exist.
     OR update translation if skill attribute changed from previous description in translation and
      return the translated skill attribute.

    Arguments:
        key_or_uuid (str): Key or uuid of the course or program needs to be translated.
        skill_attr_val (str): Value of the skill attribute that needs to be translated.
        product_type (str):

    Returns:
        str: Translated skill attribute value.
    """
    source_model_name, source_model_field = product_type, get_translation_attr(product_type)

    translation = Translation.objects.filter(
        source_model_name=source_model_name,
        source_model_field=source_model_field,
        source_record_identifier=key_or_uuid
    ).first()
    if translation:
        if translation.source_text != skill_attr_val:
            if (len(skill_attr_val.encode('utf-8'))) < AMAZON_TRANSLATION_ALLOWED_SIZE:
                result = translate_text(key_or_uuid, skill_attr_val, AUTO, ENGLISH)
            else:
                result = apply_batching_to_translate_large_text(key_or_uuid, skill_attr_val)
            if not result['TranslatedText']:
                return skill_attr_val
            if result['SourceLanguageCode'] == ENGLISH:
                translation.translated_text = skill_attr_val
            else:
                translation.translated_text = result['TranslatedText']
            LOGGER.info(f'[TAXONOMY] Translate {product_type} updated for key: {key_or_uuid}')
            translation.source_text = skill_attr_val
            translation.source_language = result['SourceLanguageCode']
            translation.save()
        return translation.translated_text
    if (len(skill_attr_val.encode('utf-8'))) < AMAZON_TRANSLATION_ALLOWED_SIZE:
        result = translate_text(key_or_uuid, skill_attr_val, AUTO, ENGLISH)
    else:
        result = apply_batching_to_translate_large_text(key_or_uuid, skill_attr_val)
    if not result['TranslatedText']:
        return skill_attr_val
    if result['SourceLanguageCode'] == ENGLISH:
        translated_text = skill_attr_val
    else:
        translated_text = result['TranslatedText']

    translation = Translation.objects.create(
        source_model_name=source_model_name,
        source_model_field=source_model_field,
        source_record_identifier=key_or_uuid,
        source_text=skill_attr_val,
        translated_text=translated_text,
        translated_text_language=ENGLISH,
        source_language=result['SourceLanguageCode'],
    )
    LOGGER.info(f'[TAXONOMY] Translate {product_type} created for key: {key_or_uuid}')
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
        message = f'[TAXONOMY] Translate (course description or program overview) exception for key: {key} Error: {ex}'
        LOGGER.exception(message)

    return result


def apply_batching_to_translate_large_text(key, source_text):
    """
    Apply batching if text to translate is large and then combine it again.

    Arguments:
        key (str): Key or id of the object to uniquely identify.
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
    LOGGER.info(f'[TAXONOMY] Translate (course description or program overview) applying batching for key: {key}')

    for sentence in sentences:
        # Translate expects utf-8 encoded input to be no more than
        # 5000 bytes, so we’ll split on the 5000th byte.

        if len(sentence.encode('utf-8')) + len(source_text_chunk.encode('utf-8')) < AMAZON_TRANSLATION_ALLOWED_SIZE:
            source_text_chunk = '%s%s' % (source_text_chunk, sentence)
        else:
            translation_chunk = translate_text(key, source_text_chunk, AUTO, ENGLISH)
            translated_text = translated_text + translation_chunk['TranslatedText']
            source_text_chunk = sentence
            source_language_code = translation_chunk['SourceLanguageCode']

    # Translate the final chunk of input text
    if source_text_chunk:
        translation_chunk = translate_text(key, source_text_chunk, AUTO, ENGLISH)
        translated_text = translated_text + translation_chunk['TranslatedText']
        source_language_code = translation_chunk['SourceLanguageCode']
    # bs4 adds /r/n which needs to be removed for consistency.
    translated_text = translated_text.replace('\r', '').replace('\n', '')
    result['TranslatedText'] = translated_text
    result['SourceLanguageCode'] = source_language_code
    return result


def duplicate_model_instance(instance):
    """
    Duplicate passed django model as described in django docs.

    https://docs.djangoproject.com/en/4.1/topics/db/queries/#copying-model-instances

        source_block (model instance): django model instance to be duplicated.
    """
    instance.id = None
    instance.pk = None
    instance._state.adding = True  # pylint: disable=protected-access
    if hasattr(instance, "created"):
        instance.created = now()
    if hasattr(instance, "modified"):
        instance.modified = now()
    instance.save()
    return instance


def delete_product(key_or_uuid: str, product_type: ProductTypes):
    """
    Delete product from database if it exists.

        key_or_uuid (str): Key or uuid of the product to be deleted.
        product_type (ProductTypes): Product type.
    """
    product_model, identifier = get_product_skill_model_and_identifier(product_type)
    product_model.objects.filter(**{identifier: key_or_uuid}).delete()


def duplicate_xblock_skills(source_xblock_uuid, xblock_uuid):
    """
    Duplicate xblock and its skills if source xblock exists.

        source_xblock_uuid (str): source xblock usage key.
        xblock_uuid (str): new xblock usage key.
    """
    # get source xblock_skill instance.
    source_xblock = XBlockSkills.objects.filter(usage_key=source_xblock_uuid).first()
    if not source_xblock:
        LOGGER.info(f'[TAXONOMY] Source xblock: {source_xblock_uuid} not found')
        return

    # just in case xblock_skill with new usage_key exists, stop execution.
    if XBlockSkills.objects.filter(usage_key=xblock_uuid).exists():
        LOGGER.error(f'[TAXONOMY] XBlock with usage_key: {xblock_uuid} already exists!')
        return

    # fetch source xblock skills.
    source_xblock_skills = XBlockSkillData.objects.filter(xblock=source_xblock).all()
    # copy source xblock with new usage_key.
    source_xblock.usage_key = xblock_uuid
    xblock = duplicate_model_instance(source_xblock)

    # copy source xblock skills and set relation with new xblock.
    for source_xblock_skill in source_xblock_skills:
        source_xblock_skill.xblock = xblock
        duplicate_model_instance(source_xblock_skill)
