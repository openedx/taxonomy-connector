"""Tests for taxonomy choice enums and backward-compatibility aliases."""

from taxonomy.choices import ProductTypes, UserGoal


def test_user_goal_legacy_aliases_map_to_enum_members():
    assert UserGoal.ChangeCareers is UserGoal.CHANGE_CAREERS
    assert UserGoal.GetPromoted is UserGoal.GET_PROMOTED
    assert UserGoal.ImproveCurrentRole is UserGoal.IMPROVE_CURRENT_ROLE
    assert UserGoal.Other is UserGoal.OTHER
    assert UserGoal.ChangeCareers.value == "change_careers"
    assert UserGoal.ChangeCareers.label == "I want to change careers"
    assert UserGoal.GetPromoted.value == "get_promoted"
    assert UserGoal.GetPromoted.label == "I want to get promoted"
    assert UserGoal.ImproveCurrentRole.value == "improve_current_role"
    assert UserGoal.ImproveCurrentRole.label == "I want to improve at my current role"
    assert UserGoal.Other.value == "other"
    assert UserGoal.Other.label == "Other"


def test_product_types_legacy_aliases_map_to_enum_members():
    assert ProductTypes.Course is ProductTypes.COURSE
    assert ProductTypes.Program is ProductTypes.PROGRAM
    assert ProductTypes.XBlock is ProductTypes.XBLOCK
    assert ProductTypes.XBlockData is ProductTypes.XBLOCKDATA
    assert ProductTypes.Course.value == "course"
    assert ProductTypes.Course.label == "Course"
    assert ProductTypes.Program.value == "program"
    assert ProductTypes.Program.label == "Program"
    assert ProductTypes.XBlock.value == "xblock"
    assert ProductTypes.XBlock.label == "XBlock"
    assert ProductTypes.XBlockData.value == "xblock_data"
    assert ProductTypes.XBlockData.label == "XBlockData"


def test_textchoices_contract_still_intact():
    assert ProductTypes.COURSE.value == "course"
    assert ProductTypes.COURSE.label == "Course"
    assert UserGoal.CHANGE_CAREERS.value == "change_careers"
    assert UserGoal.CHANGE_CAREERS.label == "I want to change careers"


def test_choices_tuples_are_stable_for_model_fields():
    assert ProductTypes.choices == [
        ("course", "Course"),
        ("program", "Program"),
        ("xblock", "XBlock"),
        ("xblock_data", "XBlockData"),
    ]
    assert UserGoal.choices == [
        ("change_careers", "I want to change careers"),
        ("get_promoted", "I want to get promoted"),
        ("improve_current_role", "I want to improve at my current role"),
        ("other", "Other"),
    ]
