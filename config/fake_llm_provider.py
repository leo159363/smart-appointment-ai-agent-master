"""Deterministic fake LLM and embedding providers for tests.

These classes are intentionally small and local. They do not read credentials,
open network connections, or call external model providers.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Iterable, Iterator, List, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult


class FakeChatModel(BaseChatModel):
    """LangChain-compatible chat model with deterministic tutoring responses."""

    temperature: float = 0.0

    @property
    def _llm_type(self) -> str:
        return "fake-chat-model"

    def bind_tools(self, tools: Any, **kwargs: Any):
        """Return self so tool-agent setup can be constructed in tests."""
        return self

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        content = self._response_for_prompt(self._messages_to_text(messages))
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content))])

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        return self._generate(messages, stop=stop, run_manager=run_manager, **kwargs)

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        content = self._response_for_prompt(self._messages_to_text(messages))
        for char in content:
            yield ChatGenerationChunk(message=AIMessageChunk(content=char))

    @staticmethod
    def _messages_to_text(messages: Iterable[Any]) -> str:
        parts: list[str] = []
        for message in messages:
            if isinstance(message, BaseMessage):
                parts.append(str(message.content))
            elif isinstance(message, dict):
                parts.append(str(message.get("content", "")))
            else:
                parts.append(str(message))
        return "\n".join(parts)

    def _response_for_prompt(self, prompt: str) -> str:
        task = self._extract_user_text(prompt)

        if self._looks_like_appointment_json_prompt(prompt):
            return self._appointment_json(task)

        if self._looks_like_yes_no_prompt(prompt):
            return "NO" if self._is_unrelated(task) or self._is_appointment(task) else "YES"

        if self._looks_like_task_classification_prompt(prompt):
            return self._classify_task(task)

        return self._consultation_answer(task)

    @staticmethod
    def _extract_user_text(prompt: str) -> str:
        labels = ("任务内容", "用户输入", "用户问题", "user_input", "task")
        matches: list[str] = []
        for label in labels:
            matches.extend(re.findall(rf"{label}\s*[：:]\s*([^\n]+)", prompt))
        if matches:
            return matches[-1].strip()
        return prompt[-500:].strip()

    @staticmethod
    def _looks_like_task_classification_prompt(prompt: str) -> bool:
        return "appointment" in prompt and "query" in prompt and "statistics" in prompt

    @staticmethod
    def _looks_like_yes_no_prompt(prompt: str) -> bool:
        return "YES" in prompt and "NO" in prompt and "用户输入" in prompt

    @staticmethod
    def _looks_like_appointment_json_prompt(prompt: str) -> bool:
        return '"start_time"' in prompt and '"project"' in prompt and '"missing_info"' in prompt

    @staticmethod
    def _is_unrelated(text: str) -> bool:
        stripped = text.strip()
        if not stripped or stripped in {"?", "？", "...", "###"}:
            return True
        unrelated_keywords = ("天气", "股票", "新闻", "好吃", "你好", "谢谢", "聊天")
        return any(keyword in stripped for keyword in unrelated_keywords)

    @staticmethod
    def _is_payment(text: str) -> bool:
        return any(keyword in text for keyword in ("支付", "付款", "购买", "买课"))

    @staticmethod
    def _is_statistics(text: str) -> bool:
        return any(keyword in text for keyword in ("统计", "完成", "反馈", "报表"))

    def _is_appointment(self, text: str) -> bool:
        if self._is_unrelated(text):
            return False
        appointment_keywords = (
            "预约",
            "排课",
            "改约",
            "请假",
            "补课",
            "周六下午",
            "明天下午",
            "固定上课",
            "找老师",
            "匹配一位",
            "帮我匹配",
            "安排试听",
        )
        if any(keyword in text for keyword in appointment_keywords):
            if any(keyword in text for keyword in ("收费", "费用", "价格", "区别")):
                return False
            return True
        return False

    def _classify_task(self, task: str) -> str:
        if self._is_unrelated(task):
            return "other"
        if self._is_payment(task):
            return "pay"
        if self._is_statistics(task):
            return "statistics"
        if self._is_appointment(task):
            return "appointment"
        return "query"

    def _appointment_json(self, user_input: str) -> str:
        unrelated = self._is_unrelated(user_input)
        project = "未知"
        if "英语" in user_input:
            project = "初中英语试听课"
        elif "数学" in user_input:
            project = "初中数学试听课"
        elif "物理" in user_input:
            project = "高中物理试听课"
        elif "试听" in user_input:
            project = "试听课"

        gender = "女" if "女老师" in user_input or "女" in user_input else "不限"
        start_time = "2026-06-09 14:00" if "2点" in user_input or "下午2" in user_input else "未知"
        if "周六下午" in user_input:
            start_time = "2026-06-13 15:00"
        elif "明天下午" in user_input:
            start_time = "2026-06-09 15:00" if start_time == "未知" else start_time

        duration = "未知"
        if "90" in user_input:
            duration = "90分钟"
        elif "120" in user_input or "两小时" in user_input or "2小时" in user_input:
            duration = "120分钟"
        elif "60" in user_input or "一小时" in user_input or "1小时" in user_input:
            duration = "60分钟"

        missing_info = []
        if start_time == "未知":
            missing_info.append("start_time")
        if project == "未知":
            missing_info.append("project")
        if duration == "未知":
            missing_info.append("duration")

        payload = {
            "gender": gender,
            "start_time": start_time,
            "duration": duration,
            "project": project,
            "preference": "基础薄弱，适合耐心细致型老师" if "基础" in user_input else "未知",
            "technician_name": "未知",
            "confirmation": "未知",
            "info_complete": not missing_info and not unrelated,
            "unrelated": unrelated,
            "missing_info": missing_info,
        }
        return json.dumps(payload, ensure_ascii=False)

    @staticmethod
    def _consultation_answer(user_input: str) -> str:
        if "10" in user_input or "20" in user_input or "课时包" in user_input or "收费" in user_input:
            return (
                "10课时包适合短期补弱、阶段冲刺或先体验学习节奏；"
                "20课时包适合系统提升、长期规划和持续跟踪。试听课需要提前预约，"
                "试听后老师会结合学生基础、年级、目标和薄弱点给出正式课程建议。"
            )
        if "线上" in user_input or "线下" in user_input:
            return "线上课适合节省通勤并使用直播互动，线下课适合需要面对面督学的学生，具体方式可在试听课前确认。"
        if "老师" in user_input or "匹配" in user_input or "基础" in user_input:
            return "老师匹配会结合年级、学科、基础薄弱点、目标分数、学习习惯和老师教学风格，优先推荐耐心细致且适合该学科的老师。"
        if "试听" in user_input or "预约" in user_input:
            return "试听课需要提前预约，课程顾问会确认年级、学科、薄弱点和可上课时间，试听后给出学习建议和正式排课方案。"
        return "我们可以提供课程咨询、老师匹配、试听课预约、正式排课和学习规划建议，建议先说明学生年级、学科和当前薄弱点。"


class FakeEmbeddingModel:
    """Deterministic embedding model for local unit tests."""

    def __init__(self, dimensions: int = 64):
        self.dimensions = dimensions

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def _embed(self, text: str) -> list[float]:
        seed = hashlib.sha256(text.encode("utf-8")).digest()
        values: list[float] = []
        counter = 0
        while len(values) < self.dimensions:
            digest = hashlib.sha256(seed + counter.to_bytes(2, "big")).digest()
            values.extend(((byte / 127.5) - 1.0) for byte in digest)
            counter += 1
        return values[: self.dimensions]
