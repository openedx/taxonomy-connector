"""
Taxonomy API serializers.
"""
from rest_framework.serializers import ModelSerializer

from taxonomy.models import CourseSkills, Job, JobPostings, JobSkills, Skill


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
    skills = JobSkillSerializer(source='jobskills_set.all', many=True)

    class Meta:
        model = Job
        fields = '__all__'
        extra_fields = ('skills',)


class CourseSkillsSerializer(ModelSerializer):

    class Meta:
        model = CourseSkills
        exclude = ('id', 'created', 'modified', 'is_blacklisted', 'skill')


class SkillListSerializer(ModelSerializer):
    courses = CourseSkillsSerializer(source='courseskills_set.all', many=True)

    class Meta:
        model = Skill
        fields = '__all__'
        extra_fields = ('courses',)


class JobPostingsSerializer(ModelSerializer):
    job = JobSerializer()

    class Meta:
        model = JobPostings
        fields = '__all__'
