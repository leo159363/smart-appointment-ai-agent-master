"""Tests for student profile memory in the /chat endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient

import api.chat_handler as chat_handler
from agents.consultant_agent import ConsultantAgent
from app import app
from services.student_profile_service import StudentProfileService


PROFILE_EXTRACTOR = StudentProfileService.__new__(StudentProfileService)


class FakeChatStudentProfileService:
    updates = []
    profiles_by_user = {}

    @classmethod
    def reset(cls):
        cls.updates = []
        cls.profiles_by_user = {}

    def extract_profile_from_text(self, text: str):
        return PROFILE_EXTRACTOR.extract_profile_from_text(text)

    def update_profile(self, user_id: str, profile_data: dict, source: str = "chat"):
        self.updates.append(
            {
                "user_id": user_id,
                "action_type": StudentProfileService.ACTION_TYPE,
                "action_data": dict(profile_data),
                "source": source,
            }
        )
        current = dict(self.profiles_by_user.get(user_id, {}))
        current.update(profile_data)
        self.profiles_by_user[user_id] = current
        return True

    def get_profile(self, user_id: str):
        return dict(self.profiles_by_user.get(user_id, {}))

    def format_profile_context(self, profile):
        return PROFILE_EXTRACTOR.format_profile_context(profile)


class FakeConsultationClassifier:
    async def is_consultation_related(self, user_input: str) -> bool:
        return True


class FakeStreamConsultationProcessor:
    def __init__(self):
        self.profile_contexts = []

    async def process_consultation_stream(
        self,
        user_input: str,
        session_id: str,
        student_profile_context: str = "",
    ):
        self.profile_contexts.append(student_profile_context)
        yield f"[REPLY][咨询机器人]fake chat answer: {student_profile_context}"


class FakeChatTaskAgent:
    def __init__(self):
        self.consultation_processor = FakeStreamConsultationProcessor()
        self.consultant_agent = ConsultantAgent()
        self.consultant_agent.consultation_classifier = FakeConsultationClassifier()
        self.consultant_agent.consultation_processor = self.consultation_processor

    async def classify_task_stream(self, user_input: str):
        async for token in self.consultant_agent.consult_stream(user_input):
            yield token


def setup_fake_chat(monkeypatch):
    fake_task_agent = FakeChatTaskAgent()
    FakeChatStudentProfileService.reset()
    monkeypatch.setattr(chat_handler, "task_agent", fake_task_agent)
    monkeypatch.setattr(chat_handler, "StudentProfileService", FakeChatStudentProfileService)
    return fake_task_agent


def test_chat_without_user_id_returns_200(monkeypatch):
    setup_fake_chat(monkeypatch)

    response = TestClient(app).post("/chat", json={"message": "试听课怎么预约？"})

    assert response.status_code == 200
    assert "fake chat answer" in response.text


def test_chat_with_user_id_returns_200(monkeypatch):
    setup_fake_chat(monkeypatch)

    response = TestClient(app).post(
        "/chat",
        json={"user_id": "chat_parent", "message": "试听课怎么预约？"},
    )

    assert response.status_code == 200
    assert "fake chat answer" in response.text


def test_chat_extracts_and_writes_student_profile(monkeypatch):
    fake_task_agent = setup_fake_chat(monkeypatch)

    response = TestClient(app).post(
        "/chat",
        json={
            "user_id": "chat_writer",
            "message": "孩子初二 数学 基础弱，周末有时间，希望老师耐心一点。",
        },
    )

    assert response.status_code == 200
    assert FakeChatStudentProfileService.updates == [
        {
            "user_id": "chat_writer",
            "action_type": "student_profile_update",
            "action_data": {
                "grade": "初二",
                "subject": "数学",
                "weak_points": "基础弱",
                "available_time": "周末",
                "teacher_style_preference": "耐心",
            },
            "source": "chat",
        }
    ]
    assert "年级：初二" in fake_task_agent.consultation_processor.profile_contexts[0]


def test_chat_reads_saved_profile_on_later_consultation(monkeypatch):
    fake_task_agent = setup_fake_chat(monkeypatch)
    client = TestClient(app)

    first_response = client.post(
        "/chat",
        json={
            "user_id": "chat_reader",
            "message": "孩子初二 数学 基础弱，周末有时间，希望老师耐心一点。",
        },
    )
    second_response = client.post(
        "/chat",
        json={"user_id": "chat_reader", "message": "试听课怎么预约？"},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert len(FakeChatStudentProfileService.updates) == 1
    assert "老师风格偏好：耐心" in fake_task_agent.consultation_processor.profile_contexts[1]
