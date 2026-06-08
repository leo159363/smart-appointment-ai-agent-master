from fastapi.testclient import TestClient

import api.consultation as consultation_api
from app import app


class FakeConsultantAgent:
    async def consult(self, question: str) -> str:
        return f"fake answer for {question}"


def test_consultation_ask_uses_consultant_agent_consult(monkeypatch):
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
    assert payload["data"]["answer"] == "fake answer for 试听课怎么预约？"
