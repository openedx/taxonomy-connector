"""
Taxonomy API serializers.
"""
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from taxonomy.models import CourseSkills, Job, JobPostings, JobSkills, Skill, SkillsQuiz


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


class SkillsQuizSerializer(ModelSerializer):
    class Meta:
        model = SkillsQuiz
        fields = '__all__'
        read_only_fields = ('username', )


class SkillsQuizBySkillNameSerializer(ModelSerializer):
    skill_names = serializers.ListField(child=serializers.CharField(), required=False)

    class Meta:
        model = SkillsQuiz
        fields = '__all__'
        read_only_fields = ('username', 'skills')

    def validate(self, attrs):
        attrs = super().validate(attrs)
        skill_names = attrs.pop('skill_names')
        attrs['skills'] = Skill.get_skill_ids_by_name(skill_names)
        return attrs

    def validate_skill_names(self, skill_names):
        valid_skill_names = Skill.objects.filter(name__in=skill_names).values_list('name', flat=True)
        if len(valid_skill_names) < len(skill_names):
            invalid_skill_names = list(set(skill_names) - set(valid_skill_names))
            raise serializers.ValidationError(f"Invalid skill names: {invalid_skill_names}")
        return skill_names
