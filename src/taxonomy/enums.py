# -*- coding: utf-8 -*-
"""
Enums used by EMSI Clients.

Enums defined here are copied from EMSI documentation at https://api.emsidata.com/apis/job-postings
"""
from enum import Enum


class RankingFacet(Enum):
    """
    Enums for categorizing the ranking of information.

    e.g. if you want get skills rankings you would use `SKILLS` enum.
    """

    CERTIFICATIONS = 'certifications'
    CERTIFICATIONS_NAME = 'certifications_name'
    CITY = 'city'
    CITY_NAME = 'city_name'
    COMPANY = 'company'
    COMPANY_NAME = 'company_name'
    COUNTY = 'county'
    COUNTY_NAME = 'county_name'
    EDULEVELS = 'edulevels'
    EDULEVELS_NAME = 'edulevels_name'
    EMPLOYMENT_TYPE = 'employment_type'
    EMPLOYMENT_TYPE_NAME = 'employment_type_name'
    FIPS = 'fips'
    FIPS_NAME = 'fips_name'
    HARD_SKILLS = 'hard_skills'
    HARD_SKILLS_NAME = 'hard_skills_name'
    MAX_YEARS_EXPERIENCE = 'max_years_experience'
    MIN_YEARS_EXPERIENCE = 'min_years_experience'
    MSA = 'msa'
    MSA_NAME = 'msa_name'
    MSA_SKILL_CLUSTER = 'msa_skill_cluster'
    NAICS2 = 'naics2'
    NAICS2_NAME = 'naics2_name'
    NAICS3 = 'naics3'
    NAICS3_NAME = 'naics3_name'
    NAICS4 = 'naics4'
    NAICS4_NAME = 'naics4_name'
    NAICS5 = 'naics5'
    NAICS5_NAME = 'naics5_name'
    NAICS6 = 'naics6'
    NAICS6_NAME = 'naics6_name'
    NATIONAL_SKILL_CLUSTER = 'national_skill_cluster'
    ONET = 'onet'
    ONET_NAME = 'onet_name'
    SKILLS = 'skills'
    SKILLS_NAME = 'skills_name'
    SOC2 = 'soc2'
    SOC2_NAME = 'soc2_name'
    SOC3 = 'soc3'
    SOC3_NAME = 'soc3_name'
    SOC4 = 'soc4'
    SOC4_NAME = 'soc4_name'
    SOC5 = 'soc5'
    SOC5_NAME = 'soc5_name'
    SOFT_SKILLS = 'soft_skills'
    SOFT_SKILLS_NAME = 'soft_skills_name'
    SOURCES = 'sources'
    STATE = 'state'
    STATE_NAME = 'state_name'
    STATE_SKILL_CLUSTER = 'state_skill_cluster'
    TITLE = 'title'
    TITLE_NAME = 'title_name'
