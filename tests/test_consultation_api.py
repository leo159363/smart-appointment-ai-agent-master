from fastapi.testclient import TestClient
import pytest

import api.consultation as consultation_api
from agents.consultant.prompt_builder import PromptBuilder
from agents.consultant_agent import ConsultantAgent
from app import app
from services.student_profile_service import StudentProfileService


PROFILE_EXTRACTOR = StudentProfileService.__new__(StudentProfileService)


class FakeApiStudentProfileService:
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


class FakeConsultantAgent:
    created_user_ids = []
    profile_contexts = []

    def __init__(self, user_id: str = "default_user", student_profile_service=None):
        self.user_id = user_id
        self.student_profile_service = student_profile_service
        self.created_user_ids.append(user_id)

    async def consult(self, question: str) -> str:
        profile_context = ""
        if self.student_profile_service:
            profile = self.student_profile_service.get_profile(self.user_id)
            if profile:
                profile_context = self.student_profile_service.format_profile_context(profile)
        self.profile_contexts.append(profile_context)
        return f"fake answer for {self.user_id}: {question}"


def patch_consultation_api(monkeypatch):
    FakeConsultantAgent.created_user_ids = []
    FakeConsultantAgent.profile_contexts = []
    FakeApiStudentProfileService.reset()
    monkeypatch.setattr(consultation_api, "ConsultantAgent", FakeConsultantAgent)
    monkeypatch.setattr(consultation_api, "StudentProfileService", FakeApiStudentProfileService)


def test_consultation_ask_uses_consultant_agent_consult(monkeypatch):
    patch_consultation_api(monkeypatch)

    client = TestClient(app)
    response = client.post(
        "/api/consultation/ask",
        json={
            "user_id": "test_parent",
            "question": "试听课怎么预约？",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["message"] == "课程咨询处理成功"
    assert payload["data"]["question"] == "试听课怎么预约？"
    assert payload["data"]["answer"] == "fake answer for test_parent: 试听课怎么预约？"
    assert FakeConsultantAgent.created_user_ids == ["test_parent"]


def test_consultation_ask_without_user_id_keeps_default_user(monkeypatch):
    patch_consultation_api(monkeypatch)

    client = TestClient(app)
    response = client.post(
        "/api/consultation/ask",
        json={"question": "试听课怎么预约？"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["answer"] == "fake answer for default_user: 试听课怎么预约？"
    assert FakeConsultantAgent.created_user_ids == ["default_user"]


def test_consultation_ask_extracts_and_writes_student_profile(monkeypatch):
    patch_consultation_api(monkeypatch)

    client = TestClient(app)
    response = client.post(
        "/api/consultation/ask",
        json={
            "user_id": "profile_writer",
            "question": "孩子初二 数学 基础弱，周末有时间，希望老师耐心一点。",
        },
    )

    assert response.status_code == 200
    assert FakeApiStudentProfileService.updates == [
        {
            "user_id": "profile_writer",
            "action_type": "student_profile_update",
            "action_data": {
                "grade": "初二",
                "subject": "数学",
                "weak_points": "基础弱",
                "available_time": "周末",
                "teacher_style_preference": "耐心",
            },
            "source": "consultation_api",
        }
    ]
    assert "年级：初二" in FakeConsultantAgent.profile_contexts[0]
    assert "学科：数学" in FakeConsultantAgent.profile_contexts[0]


def test_consultation_ask_reads_saved_profile_on_later_request(monkeypatch):
    patch_consultation_api(monkeypatch)

    client = TestClient(app)
    first_response = client.post(
        "/api/consultation/ask",
        json={
            "user_id": "profile_reader",
            "question": "孩子初二 数学 基础弱，周末有时间，希望老师耐心一点。",
        },
    )
    second_response = client.post(
        "/api/consultation/ask",
        json={
            "user_id": "profile_reader",
            "question": "试听课怎么预约？",
        },
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert len(FakeApiStudentProfileService.updates) == 1
    assert "年级：初二" in FakeConsultantAgent.profile_contexts[1]
    assert "老师风格偏好：耐心" in FakeConsultantAgent.profile_contexts[1]


def test_consultation_ask_without_profile_keywords_does_not_write_profile(monkeypatch):
    patch_consultation_api(monkeypatch)

    client = TestClient(app)
    response = client.post(
        "/api/consultation/ask",
        json={
            "user_id": "no_profile",
            "question": "试听课怎么预约？",
        },
    )

    assert response.status_code == 200
    assert FakeApiStudentProfileService.updates == []
    assert FakeConsultantAgent.profile_contexts == [""]


def test_consultation_ask_extracts_profile_for_default_user(monkeypatch):
    patch_consultation_api(monkeypatch)

    client = TestClient(app)
    response = client.post(
        "/api/consultation/ask",
        json={"question": "孩子初二 数学 基础弱，周末有时间，希望老师耐心一点。"},
    )

    assert response.status_code == 200
    assert FakeConsultantAgent.created_user_ids == ["default_user"]
    assert FakeApiStudentProfileService.updates[0]["user_id"] == "default_user"


class FakeStudentProfileService:
    def __init__(self, profile):
        self.profile = profile
        self.requested_user_id = None

    def get_profile(self, user_id: str):
        self.requested_user_id = user_id
        return self.profile

    def format_profile_context(self, profile):
        return f"学生画像：年级：{profile['grade']}；学科：{profile['subject']}"


class FakeConsultationProcessor:
    def __init__(self):
        self.student_profile_context = None

    async def process_consultation(self, question: str, student_profile_context: str = "") -> str:
        self.student_profile_context = student_profile_context
        return "ok"


@pytest.mark.asyncio
async def test_consultant_agent_reads_student_profile_context():
    profile_service = FakeStudentProfileService({"grade": "初二", "subject": "数学"})
    processor = FakeConsultationProcessor()
    agent = ConsultantAgent(user_id="profile_parent", student_profile_service=profile_service)
    agent.consultation_processor = processor

    result = await agent.consult("数学基础薄弱怎么补？")

    assert result == "ok"
    assert profile_service.requested_user_id == "profile_parent"
    assert processor.student_profile_context == "学生画像：年级：初二；学科：数学"


@pytest.mark.asyncio
async def test_consultant_agent_without_profile_keeps_original_flow():
    profile_service = FakeStudentProfileService({})
    processor = FakeConsultationProcessor()
    agent = ConsultantAgent(user_id="empty_parent", student_profile_service=profile_service)
    agent.consultation_processor = processor

    result = await agent.consult("试听课怎么预约？")

    assert result == "ok"
    assert profile_service.requested_user_id == "empty_parent"
    assert processor.student_profile_context == ""


def test_consultation_prompt_includes_profile_as_supplemental_context():
    prompt = PromptBuilder().build_consultation_prompt(
        "适合什么课程？",
        [{"content": "知识库课程规则", "category": "课程"}],
        student_profile_context="学生画像：年级：初二；学科：数学",
    )

    assert "知识库课程规则" in prompt
    assert "补充学生画像上下文" in prompt
    assert "学生画像：年级：初二；学科：数学" in prompt
