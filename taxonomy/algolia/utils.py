# -*- coding: utf-8 -*-
"""
Utility functions related to algolia indexing.
"""
import logging
from collections import deque, namedtuple
from datetime import datetime

from django.conf import settings
from django.db.models import Q, Sum

from taxonomy.algolia.client import AlgoliaClient
from taxonomy.algolia.constants import (
    ALGOLIA_JOBS_INDEX_SETTINGS,
    EMBEDDED_OBJECT_LENGTH_CAP,
    JOBS_PAGE_SIZE,
    JOBS_TO_IGNORE,
    TAXONOMY_TRANSLATION_LOCALES,
)
from taxonomy.algolia.serializers import JobSerializer
from taxonomy.models import Industry, IndustryJobSkill, Job, JobSkills, Skill, TaxonomyTranslation

LOGGER = logging.getLogger(__name__)

JobRecommendation = namedtuple('JobRecommendation', 'name similarity')


class LogTime:
    """
    Context manager to calculate and log the time taken by a piece of code.
    """
    start = None

    def __init__(self, message_prefix):
        """
        Initialize the context with the message prefix.
        """
        self.message_prefix = message_prefix

    def __enter__(self):
        """
        Start tracking the time.
        """
        self.start = datetime.now()

    def __exit__(self, *args, **kwargs):
        """
        End time tracking and log the time taken by a piece of code.
        """
        end = datetime.now()
        LOGGER.info('%s: %s', self.message_prefix, end - self.start)


def index_jobs_data_in_algolia():
    """
    Re-Index all jobs data to algolia with translations.

    This function is responsible for:
        1. Constructing a list of dicts containing all jobs present in the database (English).
        2. Creating localized variants for enabled languages (e.g., Spanish).
        3. Re-Indexing all data in a single atomic operation with zero downtime.

    Note: We need to construct a list of all jobs in the form of a list and send it all in a single attempt to
        make the operation atomic and make sure there is no downtime. Paginating DB data and incrementally adding
        objects to the index will cause downtime equal to the amount of time it will take to run the command.
    """
    client = AlgoliaClient(
        application_id=settings.ALGOLIA.get('APPLICATION_ID'),
        api_key=settings.ALGOLIA.get('API_KEY'),
        index_name=settings.ALGOLIA.get('TAXONOMY_INDEX_NAME'),
    )

    LOGGER.info('[TAXONOMY] Resetting algolia index settings from code.')
    client.set_index_settings(ALGOLIA_JOBS_INDEX_SETTINGS)

    LOGGER.info('[TAXONOMY] Fetching Jobs data from the database.')
    jobs_data = fetch_jobs_data()
    LOGGER.info('[TAXONOMY] Jobs data successfully fetched from the database.')
    LOGGER.info(f'[TAXONOMY] Total English job records: {len(jobs_data)}')

    for language in TAXONOMY_TRANSLATION_LOCALES:
        LOGGER.info(f'[TAXONOMY] Creating {language} job records.')
        localized_jobs = create_localized_job_records(jobs_data, language)
        jobs_data.extend(localized_jobs)
        LOGGER.info(f'[TAXONOMY] Added {len(localized_jobs)} {language} records.')

    LOGGER.info(f'[TAXONOMY] Total records (all languages): {len(jobs_data)}')

    LOGGER.info('[TAXONOMY] Indexing Jobs data on algolia.')
    client.replace_all_objects(jobs_data)
    LOGGER.info('[TAXONOMY] Jobs data successfully indexed on algolia.')


def calculate_jaccard_similarity(set_a, set_b):
    """
    Calculate Jaccard similarity between two sets of job skills.
    """
    try:
        return len(set_a.intersection(set_b)) / len(set_a.union(set_b))
    except ZeroDivisionError:
        return float(0)


def calculate_job_skills(jobs_qs):
    """
    Fetch and skills for each job.

    Arguments:
        jobs_qs (QuerySet): Django queryset of Job model that will be used as a starting point to fetch skills data.

    Returns:
        (dict<str: dict>): A dictionary with job name as the key and the value against each key is a dict containing
            job details, including `skills`.
    """
    job_details = {}
    for job in jobs_qs.all():
        skills = set(
            JobSkills.get_whitelisted_job_skill_qs().filter(job=job).values_list('skill__name', flat=True)
        )
        job_details[job.name] = {
            'skills': skills,
        }

    return job_details


def calculate_job_recommendations(jobs_data):
    """
    Calculate job recommendations.

    Note: `jobs_data` will be treated as mutable (instead of creating a new dict to return)
        to reduce memory footprint of this function.

    Arguments:
        jobs_data (dict<str: dict>): A dictionary containing jobs data like skills. key of the dict is jobs name and
            the value dict should at-least contain a set of skills against `skills` key.

    Returns:
        (dict<str: dict>): The same dict from the argument, with `similar_jobs` added against each job.
    """
    SIMILAR_JOBS_COUNT = 3
    for job_name, job in jobs_data.items():
        job_recommendations = deque([], maxlen=SIMILAR_JOBS_COUNT)
        for candidate_job_name, candidate_job in jobs_data.items():
            if job_name == candidate_job_name:
                continue

            jaccard_similarity = calculate_jaccard_similarity(job['skills'], candidate_job['skills'])

            insert_item_in_ordered_queue(
                queue=job_recommendations,
                item=JobRecommendation(candidate_job_name, jaccard_similarity),
                key=lambda item: item.similarity,
            )

        jobs_data[job_name]['similar_jobs'] = [item.name for item in job_recommendations]

    return jobs_data


def fetch_and_combine_job_details(jobs_qs):
    """
    Fetch data related to jobs, combine it in the form of a dict and return.

    The jobs data that we are interested in is listed below.
    1. skills: A set of skills that are associated with the corresponding job.
    2. similar_jobs: Other jobs that are similar to the corresponding job.

    Arguments:
        jobs_qs (QuerySet): Django queryset of Job model that will be used as a starting point to fetch skills data.

    Returns:
        (dict<str: dict>): A dictionary with job name as the key and the value against each key is a dict containing
            job details, including `skills` and `similar_jobs`.
    """
    with LogTime('[TAXONOMY] Time taken to fetch and combine skills data for jobs'):
        jobs_data = calculate_job_skills(jobs_qs)

    with LogTime('[TAXONOMY] Time taken to fetch and combine job recommendations'):
        jobs_data = calculate_job_recommendations(jobs_data=jobs_data)

    return jobs_data


def insert_item_in_ordered_queue(queue, item, key=lambda arg: arg):
    """
    Insert given job in the jobs list.

    `queue` is assumed to be ordered based on given key in the descending order.
    `item` is the item to insert in the list, it will be inserted in the correct place.

    Note: item will not be inserted if there is no place for it based on the key.

    Arguments:
        queue (deque<Any>): A Queue containing list of items.
        item (Any): Item that needs to be inserted.
        key (func): Optional key to get the comparable attribute of the item.
    """
    for index, element in enumerate(queue):
        if key(item) > key(element):
            if len(queue) == queue.maxlen:
                # remove the last element of the queue to avoid index error.
                queue.pop()
            queue.insert(index, item)

            # Item is inserted, return here.
            return

    # If item could not be inserted, then check for available space, and insert the item if there is space.
    if len(queue) != queue.maxlen:
        queue.append(item)
        return


def combine_industry_skills():
    """
    Constructs a dict with keys as industry names and values as their skills.
    """
    industries_and_skills = {}
    for industry in Industry.objects.all():
        # sum all significances for the same skill and then sort on total significance
        skills = list(
            IndustryJobSkill.get_whitelisted_job_skill_qs().filter(
                industry=industry
            ).values_list(
                'skill__name', flat=True
            ).annotate(
                total_significance=Sum('significance')
            ).order_by(
                '-total_significance'
            ).distinct()[:EMBEDDED_OBJECT_LENGTH_CAP]
        )
        industries_and_skills[industry.name] = skills
    return industries_and_skills


def get_job_ids(qs):
    """
     Get a set of all the job id.
    """
    batch_size = 20000
    jobs = set()

    offset, limit = 0, batch_size
    qs = qs.all()
    while qs[offset:offset + limit].exists():
        jobs = jobs.union(qs[offset:offset + limit].values_list('job_id', flat=True))
        offset = offset + limit
    return jobs


def build_name_translation_maps(language_code):
    """
    Build direct name→translation dictionaries using database queries.

    Uses database queries to map English entity names directly to translations,
    avoiding the need for two-step lookups (name→id→translation).

    Args:
        language_code: Target language (e.g., 'es')

    Returns:
        dict: {
            'job': {english_name: translated_name},
            'skill': {english_name: translated_name},
            'industry': {english_name: translated_name},
        }
    """

    LOGGER.info(f'[TAXONOMY] Building {language_code} translation maps from database.')

    # Fetch all translations for the language
    job_trans_qs = TaxonomyTranslation.objects.filter(
        content_type='job',
        language_code=language_code
    )
    skill_trans_qs = TaxonomyTranslation.objects.filter(
        content_type='skill',
        language_code=language_code
    )
    industry_trans_qs = TaxonomyTranslation.objects.filter(
        content_type='industry',
        language_code=language_code
    )

    # Build mappings: external_id to translation
    job_trans_by_id = {t.external_id: t for t in job_trans_qs}
    skill_trans_by_id = {t.external_id: t for t in skill_trans_qs}
    industry_trans_by_id = {t.external_id: t for t in industry_trans_qs}

    # Job: English name to Translated name
    job_translations = {}
    for job in Job.objects.exclude(Q(name__isnull=True) | Q(external_id__in=JOBS_TO_IGNORE)):
        trans = job_trans_by_id.get(job.external_id)
        if trans and trans.title:
            job_translations[job.name] = trans.title

    # Skill: English name to Translated name
    skill_translations = {}
    for skill in Skill.objects.exclude(external_id__isnull=True):
        trans = skill_trans_by_id.get(skill.external_id)
        if trans and trans.title:
            skill_translations[skill.name] = trans.title

    # Industry: English name to Translated name
    industry_translations = {}
    for industry in Industry.objects.exclude(code__isnull=True):
        trans = industry_trans_by_id.get(str(industry.code))
        if trans and trans.title:
            industry_translations[industry.name] = trans.title

    LOGGER.info(
        f'[TAXONOMY] Built translation maps: {len(job_translations)} jobs, '
        f'{len(skill_translations)} skills, {len(industry_translations)} industries'
    )

    return {
        'job': job_translations,
        'skill': skill_translations,
        'industry': industry_translations,
    }


def translate_skill_dict(skill, name_translation_maps):
    """
    Translate a single skill dict using direct name lookup (keeps same schema).

    Args:
        skill: Dict with skill data from JobSerializer
        name_translation_maps: Direct name→translation dictionaries

    Returns:
        Dict with translated skill data (same schema as input)
    """
    skill_name = skill.get('name', '')

    # Direct lookup: English name to Translated name
    translated_name = name_translation_maps['skill'].get(skill_name, skill_name)

    return {
        **skill,  # Copy all fields (significance, type_id, description, etc.)
        'name': translated_name,
    }


def translate_industries_array(industries, name_translation_maps):
    """
    Translate industries array with nested skills using direct name lookup (keeps same schema).

    Args:
        industries: List of industry dicts from JobSerializer
        name_translation_maps: Direct name→translation dictionaries

    Returns:
        List of translated industry dicts (same schema as input)
    """
    translated_industries = []

    for industry in industries:
        industry_name = industry.get('name', '')

        # Direct lookup: English industry name to Translated industry name
        translated_industry_name = name_translation_maps['industry'].get(industry_name, industry_name)

        # Translate nested skills (they are plain strings in current schema)
        translated_skills = [
            name_translation_maps['skill'].get(skill_name, skill_name)
            for skill_name in industry.get('skills', [])
        ]

        translated_industries.append({
            'name': translated_industry_name,
            'skills': translated_skills  # Keep as list of strings
        })

    return translated_industries


def translate_job_record(english_job, name_translation_maps, description_translation_maps, language_code):
    """
    Translate a single job record using direct name lookups - creates duplicate with same schema.

    Args:
        english_job: Dict with English job data (from JobSerializer)
        name_translation_maps: Direct name to translated_name dictionaries
        description_translation_maps: {content_type: {external_id: TaxonomyTranslation}} for descriptions
        language_code: Target language code (e.g., 'es')

    Returns:
        Dict with translated job data (SAME SCHEMA as English)
    """
    external_id = english_job.get('external_id')
    job_name = english_job.get('name', '')

    # Direct name translation
    translated_job_name = name_translation_maps['job'].get(job_name, job_name)

    # Description requires external_id lookup (not included in name maps)
    job_trans = description_translation_maps.get('job', {}).get(external_id)
    translated_description = (
        job_trans.description if (job_trans and job_trans.description)
        else english_job.get('description', '')
    )

    # Create localized copy with IDENTICAL schema
    localized_job = {
        # Metadata - change objectID for localized variant
        'objectID': f"job-{external_id}-{language_code}",
        'id': english_job.get('id'),
        'external_id': external_id,
        'metadata_language': language_code,

        # Translated top-level fields
        'name': translated_job_name,
        'description': translated_description,

        # Translate skills array (keep same schema - dicts with name, description, etc.)
        'skills': [
            translate_skill_dict(skill, name_translation_maps)
            for skill in english_job.get('skills', [])
        ],

        # Job postings (no translation - copy as-is)
        'job_postings': english_job.get('job_postings', []),

        # Translate industry_names (direct name lookup - list of strings)
        'industry_names': [
            name_translation_maps['industry'].get(ind_name, ind_name)
            for ind_name in english_job.get('industry_names', [])
        ],

        # Translate industries with nested skills (keep same schema)
        'industries': translate_industries_array(
            english_job.get('industries', []),
            name_translation_maps
        ),

        # Translate similar_jobs (direct name lookup - list of strings)
        'similar_jobs': [
            name_translation_maps['job'].get(job_name, job_name)
            for job_name in english_job.get('similar_jobs', [])
        ],

        # Non-translatable fields (copy as-is)
        'b2c_opt_in': english_job.get('b2c_opt_in', False),
        'job_sources': english_job.get('job_sources', []),
    }

    return localized_job


def create_localized_job_records(english_jobs, language_code):
    """
    Create localized variants of English job records using direct name translation.

    This function:
    1. Builds direct name→translation dictionaries (English→Spanish)
    2. Fetches description translations separately (requires external_id)
    3. Creates duplicate job records with translated content using O(1) lookups

    Args:
        english_jobs: List of serialized English job dicts
        language_code: Target language code (e.g., 'es', 'fr', 'ar')

    Returns:
        List of localized job dicts (SAME SCHEMA as English, different content)
    """

    LOGGER.info(f'[TAXONOMY] Building {language_code} translation maps.')

    # Build direct name→translation maps (job/skill/industry names)
    name_translation_maps = build_name_translation_maps(language_code)

    # Build description translation maps (requires external_id lookup)
    all_translations = TaxonomyTranslation.objects.filter(
        language_code=language_code
    )

    description_translation_maps = {
        'job': {},
        'skill': {},
        'industry': {},
    }

    for trans in all_translations:
        description_translation_maps[trans.content_type][trans.external_id] = trans

    LOGGER.info(
        f'[TAXONOMY] Loaded {len(name_translation_maps["job"])} job name, '
        f'{len(name_translation_maps["skill"])} skill name, '
        f'{len(name_translation_maps["industry"])} industry name translations.'
    )

    # Create localized variants (duplicate records with translated content)
    localized_jobs = []
    for idx, english_job in enumerate(english_jobs, 1):
        if idx % 1000 == 0:
            LOGGER.info(f'[TAXONOMY] Translated {idx}/{len(english_jobs)} jobs to {language_code}')

        localized_job = translate_job_record(
            english_job,
            name_translation_maps,
            description_translation_maps,
            language_code
        )
        localized_jobs.append(localized_job)

    LOGGER.info(f'[TAXONOMY] Completed translating {len(localized_jobs)} jobs to {language_code}')
    return localized_jobs


def fetch_jobs_data():
    """
    Construct a list of all the jobs from the database.

    Returns:
        (list<dict>): A list of dicts containing job data.
    """
    qs = Job.objects.exclude(Q(name__isnull=True) | Q(external_id__in=JOBS_TO_IGNORE))

    LOGGER.info('[TAXONOMY] Started combining skills and recommendations data for the jobs.')
    jobs_data = fetch_and_combine_job_details(qs)
    LOGGER.info('[TAXONOMY] Finished calculating job recommendations and skills.')

    with LogTime('[TAXONOMY] Time taken to combine industry skills data'):
        industry_skills = combine_industry_skills()

    start, page_size = 0, JOBS_PAGE_SIZE
    jobs = []
    LOGGER.info(f'[TAXONOMY] Started serializing Jobs data. Total Jobs: {qs.count()}')
    while qs[start:start + page_size].exists():
        job_serializer = JobSerializer(
            qs[start:start + page_size],
            many=True,
            context={
                'jobs_data': jobs_data,
                'industry_skills': industry_skills,
                'jobs_having_job_skills': get_job_ids(JobSkills.get_whitelisted_job_skill_qs()),
                'jobs_having_industry_skills': get_job_ids(IndustryJobSkill.get_whitelisted_job_skill_qs()),
            },
        )
        # Add metadata_language to English records
        for job_data in job_serializer.data:
            job_data['metadata_language'] = 'en'
        jobs.extend(job_serializer.data)
        start += page_size

    return jobs
