"""UserBehaviorAgent tests with fake LLM and in-memory behavior storage."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta

import pytest

from agents.user_behavior import BehaviorRecorder, PatternAnalyzer, PreferenceManager
from agents.user_behavior_agent import UserBehaviorAgent


class InMemoryUserBehaviorRepo:
    def __init__(self, service: "InMemoryUserBehaviorService"):
        self.service = service

    def update_user_preference(self, *args):
        if len(args) == 2:
            user_id = "default_user"
            preference_type, preference_value = args
        else:
            user_id, preference_type, preference_value = args[:3]
        self.service.update_user_preference(user_id, preference_type, preference_value)
        return True

    def get_user_preferences(self, user_id: str = "default_user", preference_type: str | None = None):
        values = {
            item["preference_type"]: item["preference_value"]
            for item in self.service.get_user_preferences(user_id)
            if preference_type is None or item["preference_type"] == preference_type
        }
        return values

    def get_user_behaviors(self, action_type: str | None = None, days_back: int | None = None):
        return self.service.get_user_behaviors("default_user", action_type, days_back)

    def get_user_statistics(self, days_back: int = 30):
        behaviors = self.get_user_behaviors(days_back=days_back)
        return {"total_behaviors": len(behaviors)}


class InMemoryUserBehaviorService:
    def __init__(self):
        self.behaviors: list[dict] = []
        self.preferences: list[dict] = []
        self.user_behavior_repo = InMemoryUserBehaviorRepo(self)

    def record_behavior(
        self,
        user_id: str,
        action_type: str,
        action_data: dict | None = None,
        technician_id: str | int | None = None,
        session_id: str = "default_session",
    ) -> bool:
        if not action_type:
            return False

        created_at = (action_data or {}).get("timestamp") or datetime.now()
        self.behaviors.append(
            {
                "id": len(self.behaviors) + 1,
                "user_id": user_id,
                "action_type": action_type,
                "action_data": action_data or {},
                "technician_id": technician_id,
                "session_id": session_id,
                "created_at": created_at,
            }
        )
        return True

    def get_user_behaviors(
        self,
        user_id: str,
        action_type: str | None = None,
        days_back: int | None = None,
    ) -> list[dict]:
        rows = [
            item
            for item in self.behaviors
            if item["user_id"] == user_id and (action_type is None or item["action_type"] == action_type)
        ]
        if days_back is not None:
            cutoff = datetime.now() - timedelta(days=days_back)
            rows = [item for item in rows if item["created_at"] >= cutoff]
        return sorted(rows, key=lambda item: item["created_at"], reverse=True)

    def get_user_preferences(self, user_id: str) -> list[dict]:
        return [item for item in self.preferences if item["user_id"] == user_id]

    def update_user_preference(
        self,
        user_id: str,
        preference_type: str,
        preference_value: str,
        confidence_score: int = 1,
    ) -> bool:
        for item in self.preferences:
            if (
                item["user_id"] == user_id
                and item["preference_type"] == preference_type
                and item["preference_value"] == preference_value
            ):
                item["confidence_score"] += confidence_score
                item["last_updated"] = datetime.now()
                return True

        self.preferences.append(
            {
                "id": len(self.preferences) + 1,
                "user_id": user_id,
                "preference_type": preference_type,
                "preference_value": preference_value,
                "confidence_score": confidence_score,
                "last_updated": datetime.now(),
            }
        )
        return True


def build_agent_with_fake_behavior_store() -> tuple[UserBehaviorAgent, InMemoryUserBehaviorService]:
    service = InMemoryUserBehaviorService()
    agent = UserBehaviorAgent()
    agent._user_behavior_service = service
    agent.behavior_service = service
    agent.pattern_analyzer = PatternAnalyzer(service)
    agent.behavior_recorder = BehaviorRecorder(service)
    agent.preference_manager = PreferenceManager(service)
    return agent, service


class TestUserBehaviorAgentCoreFeatures:
    def test_should_record_user_behavior_correctly(self):
        agent, service = build_agent_with_fake_behavior_store()

        result = agent.record_behavior(
            action_type="appointment",
            action_data={"project": "初中英语试听课", "duration": "90分钟"},
            technician_id=101,
            session_id="test_session",
        )

        assert result is True
        assert len(service.behaviors) == 1
        assert service.behaviors[0]["action_type"] == "appointment"
        assert service.behaviors[0]["action_data"]["project"] == "初中英语试听课"

    def test_should_analyze_user_preferences_correctly(self):
        agent, _ = build_agent_with_fake_behavior_store()

        for project in ["初中数学试听课", "初中数学试听课", "高中物理试听课"]:
            agent.record_behavior(
                action_type="appointment",
                action_data={"project": project, "duration": "90分钟"},
                technician_id=101,
            )

        analysis = agent.get_user_analysis("default_user")

        assert analysis is not None
        assert analysis["favorite_technician_id"] == 101
        assert analysis["favorite_service"] == "初中数学试听课"
        assert analysis["favorite_duration"] == "90分钟"
        assert analysis["total_appointments"] == 3

    @pytest.mark.asyncio
    async def test_should_generate_personalized_recommendations(self):
        agent, _ = build_agent_with_fake_behavior_store()
        agent.record_behavior(
            action_type="appointment",
            action_data={"project": "数学基础补弱课", "duration": "90分钟"},
            technician_id=999,
        )

        message = await agent.generate_personalized_reminder(
            "default_user",
            available_times=[{"formatted": "今天19:00"}],
        )

        assert isinstance(message, str)
        assert len(message.strip()) > 0
        assert "老师" in message or "课程" in message or "学习" in message

    def test_should_identify_behavior_patterns(self):
        agent, service = build_agent_with_fake_behavior_store()
        base_time = datetime.now() - timedelta(days=20)

        for index in range(4):
            agent.record_behavior(
                action_type="appointment",
                action_data={
                    "project": "初中数学试听课",
                    "duration": "90分钟",
                    "timestamp": base_time + timedelta(days=index),
                },
            )
        agent.record_behavior(
            action_type="consultation",
            action_data={"question": "数学基础弱怎么提升"},
        )

        recent = service.get_user_behaviors("default_user", days_back=30)
        counts = Counter(item["action_type"] for item in recent)

        assert counts["appointment"] == 4
        assert counts["consultation"] == 1

    def test_should_provide_behavior_insights(self):
        agent, _ = build_agent_with_fake_behavior_store()

        message = agent.generate_reminder_message("brand_new_user")

        assert isinstance(message, str)
        assert len(message.strip()) > 0
        assert "预约" in message or "试听" in message or "课程" in message


class TestUserBehaviorAgentDataManagement:
    def test_should_manage_user_preferences_storage(self):
        agent, _ = build_agent_with_fake_behavior_store()

        agent.preference_manager.update_service_preference("高中物理试听课")
        agent.preference_manager.update_duration_preference("90分钟")

        summary = agent.preference_manager.get_preference_summary()

        assert summary["has_service_preference"] is True
        assert summary["has_duration_preference"] is True
        assert summary["preferred_service"] == "高中物理试听课"
        assert summary["preferred_duration"] == "90分钟"

    def test_should_handle_data_aggregation(self):
        agent, service = build_agent_with_fake_behavior_store()

        projects = ["初中数学试听课", "初中数学试听课", "高中物理试听课"]
        for project in projects:
            agent.record_behavior(
                action_type="appointment",
                action_data={"project": project, "duration": "60分钟"},
            )

        project_counts = Counter(
            item["action_data"].get("project")
            for item in service.get_user_behaviors("default_user", action_type="appointment")
        )

        assert project_counts["初中数学试听课"] == 2
        assert project_counts["高中物理试听课"] == 1

    def test_should_handle_privacy_and_data_cleanup(self):
        agent, _ = build_agent_with_fake_behavior_store()

        valid = agent.behavior_recorder.validate_behavior_data(
            "appointment",
            {"start_time": "2026-06-09 19:00", "duration": "90分钟"},
        )
        invalid = agent.behavior_recorder.validate_behavior_data("appointment", {"duration": "90分钟"})
        deleted_count = agent.behavior_recorder.delete_old_behaviors(days_to_keep=365)

        assert valid is True
        assert invalid is False
        assert deleted_count == 0


class TestUserBehaviorAgentEdgeCases:
    def test_should_handle_new_user_with_no_history(self):
        agent, _ = build_agent_with_fake_behavior_store()

        analysis = agent.get_user_analysis("brand_new_user")
        message = agent.generate_reminder_message("brand_new_user")

        assert analysis is None
        assert isinstance(message, str)
        assert len(message.strip()) > 0

    def test_should_handle_invalid_behavior_data(self):
        agent, _ = build_agent_with_fake_behavior_store()

        assert agent.record_behavior(action_type="", action_data={}) is False
        assert agent.behavior_recorder.validate_behavior_data("consultation", {"question": "试听课规则"}) is True
        assert agent.behavior_recorder.validate_behavior_data("consultation", {}) is False
