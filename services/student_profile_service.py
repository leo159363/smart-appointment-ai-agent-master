"""Student profile memory service backed by existing user behavior events."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, Mapping, Optional

from services.user_behavior_service import UserBehaviorService


class StudentProfileService:
    """Stores student profile updates without introducing a new table."""

    ACTION_TYPE = "student_profile_update"
    PROFILE_FIELDS = (
        "grade",
        "subject",
        "weak_points",
        "learning_goal",
        "available_time",
        "teacher_style_preference",
    )
    FIELD_LABELS = {
        "grade": "年级",
        "subject": "学科",
        "weak_points": "薄弱点",
        "learning_goal": "学习目标",
        "available_time": "可上课时间",
        "teacher_style_preference": "老师风格偏好",
    }
    KEYWORD_RULES = {
        "grade": ("初一", "初二", "初三", "高一", "高二", "高三"),
        "subject": ("数学", "英语", "物理", "化学", "语文"),
        "weak_points": ("基础薄弱", "基础弱", "计算粗心", "阅读理解弱", "考试焦虑"),
        "learning_goal": ("补基础", "提分", "冲刺", "系统提升"),
        "available_time": ("周末", "周六", "周日", "晚上", "下午"),
        "teacher_style_preference": ("冲刺型", "互动型", "口语型", "耐心", "严格"),
    }

    def __init__(
        self,
        behavior_service: Optional[UserBehaviorService] = None,
        db_path: str = "sqlite:///data/smart_appointment.db",
    ):
        self.behavior_service = behavior_service or UserBehaviorService(db_path=db_path)

    def extract_profile_from_text(self, text: str) -> Dict[str, str]:
        """Extract a minimal profile from user text with deterministic rules."""
        if not text:
            return {}

        profile: Dict[str, str] = {}
        text_value = str(text)
        for field, keywords in self.KEYWORD_RULES.items():
            matches = self._find_keywords(text_value, keywords)
            if matches:
                profile[field] = "、".join(matches)
        return profile

    def update_profile(
        self,
        user_id: str,
        profile_data: Mapping[str, Any],
        source: str = "chat",
    ) -> bool:
        """Write a student profile update event into user_behaviors."""
        normalized = self._normalize_profile_data(profile_data)
        if not user_id or not normalized:
            return False

        return self.behavior_service.record_behavior(
            user_id=user_id,
            action_type=self.ACTION_TYPE,
            action_data=normalized,
            session_id=source or "chat",
        )

    def get_profile(self, user_id: str) -> Dict[str, str]:
        """Merge profile update events for a user into the latest profile."""
        if not user_id:
            return {}

        behaviors = self.behavior_service.get_user_behaviors(
            user_id=user_id,
            action_type=self.ACTION_TYPE,
        )
        profile: Dict[str, str] = {}
        for behavior in sorted(behaviors, key=self._created_at_sort_key):
            action_data = behavior.get("action_data") or {}
            if isinstance(action_data, Mapping):
                profile.update(self._normalize_profile_data(action_data))
        return profile

    def format_profile_context(self, profile: Mapping[str, Any]) -> str:
        """Format a compact profile context suitable for prompt injection."""
        normalized = self._normalize_profile_data(profile)
        if not normalized:
            return ""

        parts = [
            f"{self.FIELD_LABELS[field]}：{normalized[field]}"
            for field in self.PROFILE_FIELDS
            if field in normalized
        ]
        return "学生画像：" + "；".join(parts)

    def _normalize_profile_data(self, profile_data: Mapping[str, Any]) -> Dict[str, str]:
        normalized: Dict[str, str] = {}
        if not isinstance(profile_data, Mapping):
            return normalized

        for field in self.PROFILE_FIELDS:
            value = self._clean_value(profile_data.get(field))
            if value:
                normalized[field] = value
        return normalized

    def _clean_value(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, Iterable) and not isinstance(value, (bytes, bytearray, Mapping)):
            parts = [str(item).strip() for item in value if str(item).strip()]
            return "、".join(parts)
        return str(value).strip()

    def _find_keywords(self, text: str, keywords: Iterable[str]) -> list[str]:
        return [keyword for keyword in keywords if keyword in text]

    def _created_at_sort_key(self, behavior: Mapping[str, Any]) -> datetime:
        created_at = behavior.get("created_at")
        if isinstance(created_at, datetime):
            return created_at
        if isinstance(created_at, str):
            try:
                return datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except ValueError:
                return datetime.min
        return datetime.min
