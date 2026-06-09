"""StudentProfileService tests with an isolated SQLite database."""

from __future__ import annotations

from pathlib import Path

from services.student_profile_service import StudentProfileService
from services.user_behavior_service import UserBehaviorService


def build_service(tmp_path: Path) -> StudentProfileService:
    db_url = f"sqlite:///{(tmp_path / 'student_profile.db').as_posix()}"
    behavior_service = UserBehaviorService(db_path=db_url)
    return StudentProfileService(behavior_service=behavior_service)


def test_should_extract_profile_fields_from_text(tmp_path):
    service = build_service(tmp_path)

    profile = service.extract_profile_from_text(
        "孩子初二数学基础薄弱，想补基础，周末下午有时间，希望老师耐心一点。"
    )

    assert profile == {
        "grade": "初二",
        "subject": "数学",
        "weak_points": "基础薄弱",
        "learning_goal": "补基础",
        "available_time": "周末、下午",
        "teacher_style_preference": "耐心",
    }


def test_should_write_profile_update_event(tmp_path):
    service = build_service(tmp_path)

    result = service.update_profile(
        "parent_001",
        {"grade": "初三", "subject": "英语", "weak_points": "阅读理解弱"},
        source="test",
    )

    assert result is True
    behaviors = service.behavior_service.get_user_behaviors(
        "parent_001",
        action_type=StudentProfileService.ACTION_TYPE,
    )
    assert len(behaviors) == 1
    assert behaviors[0]["action_type"] == "student_profile_update"
    assert behaviors[0]["action_data"] == {
        "grade": "初三",
        "subject": "英语",
        "weak_points": "阅读理解弱",
    }
    assert behaviors[0]["session_id"] == "test"


def test_should_merge_latest_profile_updates(tmp_path):
    service = build_service(tmp_path)

    assert service.update_profile("parent_002", {"grade": "高一", "subject": "物理"})
    assert service.update_profile(
        "parent_002",
        {
            "subject": "化学",
            "learning_goal": "冲刺",
            "teacher_style_preference": "严格",
        },
    )

    profile = service.get_profile("parent_002")

    assert profile == {
        "grade": "高一",
        "subject": "化学",
        "learning_goal": "冲刺",
        "teacher_style_preference": "严格",
    }


def test_should_return_empty_profile_for_new_user(tmp_path):
    service = build_service(tmp_path)

    assert service.get_profile("new_parent") == {}
    assert service.update_profile("new_parent", {}) is False


def test_should_format_profile_context_safely(tmp_path):
    service = build_service(tmp_path)

    context = service.format_profile_context(
        {
            "grade": "高三",
            "subject": "数学",
            "weak_points": None,
            "learning_goal": "提分",
            "available_time": "",
            "teacher_style_preference": "冲刺型",
            "user_id": "default_user",
        }
    )

    assert context == "学生画像：年级：高三；学科：数学；学习目标：提分；老师风格偏好：冲刺型"
    assert "None" not in context
    assert "undefined" not in context
    assert "default_user" not in context
