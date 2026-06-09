from fastapi.testclient import TestClient
import pytest

import api.consultation as consultation_api
from agents.consultant.prompt_builder import PromptBuilder
from agents.consultant_agent import ConsultantAgent
from app import app


class FakeConsultantAgent:
    created_user_ids = []

    def __init__(self, user_id: str = "default_user"):
        self.user_id = user_id
        self.created_user_ids.append(user_id)

    async def consult(self, question: str) -> str:
        return f"fake answer for {self.user_id}: {question}"


def test_consultation_ask_uses_consultant_agent_consult(monkeypatch):
    FakeConsultantAgent.created_user_ids = []
    monkeypatch.setattr(consultation_api, "ConsultantAgent", FakeConsultantAgent)

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
    FakeConsultantAgent.created_user_ids = []
    monkeypatch.setattr(consultation_api, "ConsultantAgent", FakeConsultantAgent)

    client = TestClient(app)
    response = client.post(
        "/api/consultation/ask",
        json={"question": "试听课怎么预约？"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["answer"] == "fake answer for default_user: 试听课怎么预约？"
    assert FakeConsultantAgent.created_user_ids == ["default_user"]


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
