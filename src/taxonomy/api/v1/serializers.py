"""
Taxonomy API serializers.
"""
import logging

from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from taxonomy.models import (
    CourseSkills,
    Job,
    JobPath,
    JobPostings,
    JobSkills,
    Skill,
    SkillCategory,
    SkillsQuiz,
    SkillSubCategory,
    XBlockSkillData,
    XBlockSkills,
)
from taxonomy.utils import generate_and_store_job_to_job_description

LOGGER = logging.getLogger(__name__)


class JobSerializer(ModelSerializer):

    class Meta:
        model = Job
        fields = '__all__'


class SkillSerializer(ModelSerializer):

    class Meta:
        model = Skill
        fields = '__all__'


class JobSkillSerializer(ModelSerializer):
    skill = SkillSerializer()

    class Meta:
        model = JobSkills
        exclude = ('id', 'created', 'modified', 'job')


class JobsListSerializer(ModelSerializer):
    skills = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = '__all__'
        extra_fields = ('skills',)

    def get_skills(self, instance):
        """
        Get JobSkill records.
        """
        return JobSkillSerializer(
            JobSkills.get_whitelisted_job_skill_qs().filter(job=instance),
            many=True,
        ).data


class CourseSkillsSerializer(ModelSerializer):

    class Meta:
        model = CourseSkills
        exclude = ('id', 'created', 'modified', 'is_blacklisted', 'skill')


class XBlockSkillDataSerializer(ModelSerializer):
    usage_key = serializers.CharField(source='xblock.usage_key')

    class Meta:
        model = XBlockSkillData
        exclude = ('id', 'created', 'modified', 'is_blacklisted', 'skill', 'xblock')


class SkillListSerializer(ModelSerializer):
    courses = CourseSkillsSerializer(source='courseskills_set.all', many=True)
    xblocks = XBlockSkillDataSerializer(source='xblockskilldata_set.all', many=True)

    class Meta:
        model = Skill
        fields = '__all__'
        extra_fields = ('courses', 'xblocks')


class JobPostingsSerializer(ModelSerializer):
    job = JobSerializer()

    class Meta:
        model = JobPostings
        fields = '__all__'


class SkillsQuizSerializer(ModelSerializer):
    class Meta:
        model = SkillsQuiz
        fields = '__all__'
        read_only_fields = ('username', )


class CurrentJobSerializer(ModelSerializer):
    """
    Serializer to get only id and name of current job.
    """

    current_job = serializers.IntegerField(read_only=True)

    class Meta:
        model = SkillsQuiz
        fields = ('username', 'current_job')


class ShortSkillSerializer(ModelSerializer):
    """
    Serializer to get only id and name of skills.
    """
    class Meta:
        model = Skill
        fields = ('id', 'name')


class XBlocksSkillsSerializer(ModelSerializer):
    """
    Serializer to get XBlockSkills fields.
    """
    skills = ShortSkillSerializer(many=True)

    class Meta:
        model = XBlockSkills
        exclude = ('created', 'modified')


class ShortSkillSubcategorySerializer(ModelSerializer):
    """
    Serializer to get only id, name and skills of SkillSubcategory.
    """
    skills = ShortSkillSerializer(source='skill_set', many=True)

    class Meta:
        model = SkillSubCategory
        fields = ('id', 'name', 'skills')


class SkillCategorySerializer(ModelSerializer):
    """
    Serializer to get SkillCategory fields.
    """
    skills = ShortSkillSerializer(source='skill_set', many=True)
    skills_subcategories = ShortSkillSubcategorySerializer(source='skillsubcategory_set', many=True)

    class Meta:
        model = SkillCategory
        fields = ('id', 'name', 'skills', 'skills_subcategories')


class JobSkillCategorySerializer(ModelSerializer):
    """
    Serializer to get data for JobTopSkillCategoriesAPIView.
    """
    skill_categories = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = ('id', 'name', 'skill_categories')

    def get_skill_categories(self, __):
        """get skill_categories queryset from context and serializing it using SkillCategorySerializer."""
        return SkillCategorySerializer(
            self.context['skill_categories'], many=True
        ).data


class JobPathSerializer(serializers.Serializer):
    """
    Serializer for JobPathAPIView.
    """
    current_job = serializers.SlugRelatedField(
        queryset=Job.objects.all(),
        required=True,
        slug_field='external_id',
        error_messages={
            'does_not_exist': 'Job with external_id={value} does not exist.',
        }
    )
    future_job = serializers.SlugRelatedField(
        queryset=Job.objects.all(),
        required=True,
        slug_field='external_id',
        error_messages={
            'does_not_exist': 'Job with external_id={value} does not exist.',
        }
    )

    def validate(self, data):
        """
        Validates that current job and future job must not be same.
        """
        if data['current_job'] == data['future_job']:
            raise serializers.ValidationError(
                'Current and Future jobs can not be same.'
            )
        return data

    def create(self, validated_data):
        """
        Create JobPath objects.
        """
        current_job = validated_data['current_job']
        future_job = validated_data['future_job']

        try:
            return JobPath.objects.get(current_job=current_job, future_job=future_job)
        except JobPath.DoesNotExist:
            LOGGER.info(
                "JobPath does not exist. CurrentJob: [%s], FutureJob: [%s]",
                current_job.name,
                future_job.name
            )
            return generate_and_store_job_to_job_description(current_job, future_job)
