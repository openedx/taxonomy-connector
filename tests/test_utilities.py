"""
Validate that utility functions are working properly.
"""
from pytest import mark

from taxonomy import models, utils
from test_utils import factories
from test_utils.constants import COURSE_KEY
from test_utils.testcase import TaxonomyTestCase


@mark.django_db
class TestUtils(TaxonomyTestCase):
    """
    Validate utility functions.
    """

    def setUp(self):
        """
        Instantiate skills and other objects for tests.
        """
        super(TestUtils, self).setUp()
        self.skill = factories.SkillFactory()

    def test_black_list_course_skill(self):
        """
        Validate that black_list_course_skill works as expected.
        """
        utils.black_list_course_skill(course_key=COURSE_KEY, skill_id=self.skill.id)

        assert models.BlacklistedCourseSkill.objects.filter(
            course_id=COURSE_KEY, skill_id=self.skill.id
        ).exists()

        assert not models.BlacklistedCourseSkill.objects.filter(
            course_id=COURSE_KEY, skill_id=0
        ).exists()

        assert not models.BlacklistedCourseSkill.objects.filter(
            course_id='invalid+course-key', skill_id=self.skill.id
        ).exists()

        skill = factories.SkillFactory()

        assert not models.BlacklistedCourseSkill.objects.filter(
            course_id=COURSE_KEY, skill_id=skill.id
        ).exists()

    def test_is_course_skill_black_listed(self):
        """
        Validate that is_course_skill_black_listed works as expected.
        """
        utils.black_list_course_skill(course_key=COURSE_KEY, skill_id=self.skill.id)

        assert utils.is_course_skill_black_listed(COURSE_KEY, self.skill.id) is True
        assert utils.is_course_skill_black_listed(COURSE_KEY, 0) is not True
        assert utils.is_course_skill_black_listed('invalid+course-key', self.skill.id) is not True

        skill = factories.SkillFactory()
        assert utils.is_course_skill_black_listed(COURSE_KEY, skill.id) is not True

    def test_update_skills_data(self):
        """
        Validate that update_skills_data works as expected.
        """
        black_listed_course_skill = factories.BlacklistedCourseSkillFactory(course_id=COURSE_KEY)

        utils.update_skills_data(
            course_key=COURSE_KEY,
            confidence=0.9,
            skill_data={
                'external_id': black_listed_course_skill.skill.external_id,
                'name': black_listed_course_skill.skill.name,
                'info_url': black_listed_course_skill.skill.info_url,
                'type_id': black_listed_course_skill.skill.type_id,
                'type_name': black_listed_course_skill.skill.type_name,
            }
        )
        utils.update_skills_data(
            course_key=COURSE_KEY,
            confidence=0.9,
            skill_data={
                'external_id': self.skill.external_id,
                'name': self.skill.name,
                'info_url': self.skill.info_url,
                'type_id': self.skill.type_id,
                'type_name': self.skill.type_name,
            }
        )

        # Make sure black listed skill is not added to `CourseSkills`.
        assert utils.is_course_skill_black_listed(COURSE_KEY, black_listed_course_skill.skill.id) is True
        assert not models.CourseSkills.objects.filter(
            course_id=COURSE_KEY,
            skill=black_listed_course_skill.skill,
        ).exists()

        # Make sure that skill that was not black listed is added with no issues/
        assert utils.is_course_skill_black_listed(COURSE_KEY, self.skill.id) is False
        assert models.CourseSkills.objects.filter(
            course_id=COURSE_KEY,
            skill=self.skill,
        ).exists()
