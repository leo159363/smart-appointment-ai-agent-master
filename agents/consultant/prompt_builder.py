"""
提示词构建器

负责构建各种类型的提示词
"""

from typing import List, Dict, Any


class PromptBuilder:
    """提示词构建器"""
    
    def __init__(self):
        self.system_prompt = self._create_system_prompt()
        self.classification_prompt_template = self._create_classification_prompt_template()
    
    def _create_system_prompt(self) -> str:
        """创建系统提示词"""
        return (
            "你是家教培训机构的课程咨询顾问，负责为学生和家长解答课程咨询、老师匹配、试听课预约、正式排课、收费规则和学习规划等问题。"
            "我会为你提供相关的知识库信息，请基于这些信息来回答用户的问题。"
            "如果知识库中没有相关信息，请提供合理的兜底回答，比如："
            "- 对于课程体系问题：可以先说明我们会根据学生年级、薄弱科目和学习目标推荐一对一或专项课程。"
            "- 对于老师匹配问题：可以说明会结合科目、年级、教学风格、可上课时间和学生性格进行匹配。"
            "- 对于试听课问题：可以说明试听课用于诊断基础、体验老师风格和确认后续学习方案。"
            "- 对于收费或课时包问题：不要只说没有统一标价。即使知识库信息不足，也要给出规则型回答：试听课需要提前预约；正式课程通常按年级、学科难度、老师类型、课时长度和课时包方案确认；10课时包适合短期补弱或阶段冲刺，20课时包适合系统提升；试听后由教务老师结合课程方案确认具体价格和排课安排。"
            "- 对于退费、请假或补课问题：如果知识库信息不足，请提示需要按机构规则、合同约定和剩余课时核对。"
            "- 对于校区或线上课问题：如果知识库信息不足，请建议联系课程顾问确认具体校区、线上平台或上课方式。"
            "- 对于家长沟通和课后反馈问题：可以说明老师或课程顾问会反馈课堂表现、作业建议和阶段学习重点。"
            "请用专业、礼貌、简洁的语言回复用户。"
            "如果用户的问题与家教课程咨询和排课完全无关（如股票、新闻、闲聊等），请礼貌地告知用户你只能回答课程、老师、试听、排课、收费和学习规划相关问题。"
            "回答时要自然流畅，不要明显地表现出是在查阅资料。"
        )
    
    def _create_classification_prompt_template(self) -> str:
        """创建分类提示词模板"""
        return (
            "你是一个分类器，判断用户输入是否是关于家教培训机构的咨询类问题。\n"
            "咨询类问题包括：课程体系、适合年级、老师介绍、教学风格、收费规则、课时包、试听课规则、正式排课规则、请假补课、退费规则、线上课、线下校区、家长沟通、课后反馈和学习规划等。\n"
            "非咨询类问题包括：明确要求预约或排课（我要预约、帮我安排、改约等）、取消预约、股票、新闻、闲聊等完全无关的话题。\n"
            "如果是咨询类问题，回答'YES'。如果是预约排课类问题或完全无关问题，回答'NO'。\n"
            "只回答YES或NO。\n\n"
            "用户输入：{user_input}"
        )
    
    def build_consultation_prompt(
        self,
        user_input: str,
        knowledge_docs: List[Dict[str, Any]],
        student_profile_context: str = "",
    ) -> str:
        """构建咨询提示词"""
        context = self._build_knowledge_context(knowledge_docs)
        profile_context = ""
        if student_profile_context:
            profile_context = f"\n补充学生画像上下文（仅作为个性化参考，不替代知识库信息）：\n{student_profile_context}\n"
        return f"{self.system_prompt}\n\n{context}{profile_context}\n用户问题：{user_input}\n\n请回答用户的问题。"
    
    def build_classification_prompt(self, user_input: str) -> str:
        """构建分类提示词"""
        return self.classification_prompt_template.format(user_input=user_input)
    
    def _build_knowledge_context(self, knowledge_docs: List[Dict[str, Any]]) -> str:
        """构建知识库上下文"""
        if not knowledge_docs:
            return "没有找到直接相关的知识库信息，请基于你对家教培训机构课程咨询、老师匹配和排课流程的一般了解回答。"
        
        context = "\n以下是相关的知识库信息：\n"
        for i, doc in enumerate(knowledge_docs, 1):
            context += f"{i}. {doc['content']}\n"
        context += "\n请基于以上信息回答用户问题。如果知识库信息不足以回答问题，请基于你对家教培训机构课程咨询、老师匹配和排课流程的一般了解来补充回答。\n"
        
        return context
