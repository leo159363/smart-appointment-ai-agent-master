"""
响应生成器

负责生成AI响应内容
"""

from typing import Dict, Any, AsyncGenerator
from langchain_core.language_models.chat_models import BaseChatModel
from .prompt_builder import PromptBuilder


class ResponseGenerator:
    """响应生成器"""
    
    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        self.prompt_builder = PromptBuilder()
    
    async def generate_response(self, user_input: str, knowledge_docs: list, student_profile_context: str = "") -> str:
        """生成标准响应"""
        try:
            prompt = self.prompt_builder.build_consultation_prompt(
                user_input,
                knowledge_docs,
                student_profile_context=student_profile_context,
            )
            response = await self.llm.ainvoke([{"role": "user", "content": prompt}])
            return self._enhance_pricing_response(user_input, response.content)
        except Exception as e:
            if self._is_pricing_query(user_input):
                return self._pricing_fallback_response()
            return f"抱歉，处理您的问题时出现了错误。请稍后再试。"
    
    async def generate_response_stream(
        self,
        user_input: str,
        knowledge_docs: list,
        student_profile_context: str = "",
    ) -> AsyncGenerator[str, None]:
        """生成流式响应"""
        try:
            prompt = self.prompt_builder.build_consultation_prompt(
                user_input,
                knowledge_docs,
                student_profile_context=student_profile_context,
            )
            response = await self.llm.ainvoke([{"role": "user", "content": prompt}])
            content = self._enhance_pricing_response(user_input, response.content)
            
            # 只在开头添加一次REPLY标签，然后逐字符输出
            yield "[REPLY][咨询机器人]"
            for char in content:
                yield char
                
        except Exception as e:
            error_msg = self._pricing_fallback_response() if self._is_pricing_query(user_input) else f"抱歉，处理您的问题时出现了错误：{str(e)}"
            yield "[REPLY][咨询机器人]"
            for char in error_msg:
                yield char
    
    def create_unrelated_message(self) -> str:
        """创建与咨询无关的回复消息"""
        return "[THOUGHT][咨询机器人] 咨询机器人：这个问题不是咨询类问题，我将转回给归类机器人处理。"

    def _is_pricing_query(self, user_input: str) -> bool:
        """判断是否为收费或课时包咨询"""
        keywords = ["收费", "费用", "价格", "多少钱", "课时包", "课程包", "10课时", "20课时", "试听课"]
        return any(keyword in user_input for keyword in keywords)

    def _enhance_pricing_response(self, user_input: str, content: str) -> str:
        """避免收费类回答只停留在没有统一标价"""
        if not self._is_pricing_query(user_input):
            return content

        weak_phrases = ["暂未提供统一标价", "没有统一标价", "知识库中暂未", "无法提供具体价格"]
        has_package_rule = "10课时" in content or "20课时" in content or "课时包" in content
        if has_package_rule and not any(phrase in content for phrase in weak_phrases):
            return content

        return self._pricing_fallback_response()

    def _pricing_fallback_response(self) -> str:
        """收费类问题的规则型兜底回答"""
        return (
            "试听课需要提前预约，具体体验方式和费用以机构当前规则为准。"
            "正式课程通常会结合学生年级、学科难度、老师类型、课时长度和课时包方案确认价格。"
            "10课时包更适合短期补弱、考前冲刺或阶段性查漏补缺；20课时包更适合系统提升、长期规划和持续跟进。"
            "建议先安排试听课，老师根据学生基础和学习目标给出课程方案后，再由教务老师确认正式报价和排课安排。"
        )
