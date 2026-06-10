"""
消息构建器

负责构建各种响应消息
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class MessageBuilder:
    """消息构建器"""
    
    def __init__(self):
        self.field_labels = {
            "gender": "老师性别偏好",
            "start_time": "具体上课时间",
            "duration": "课程时长",
            "project": "课程/学科",
            "preference": "学习需求或老师风格偏好",
            "service_type": "课程类型",
            "appointment_time": "上课时间",
            "technician_id": "老师 ID",
            "technician": "老师",
            "user_id": "学生/家长"
        }
        self.missing_info_prompts = {
            "gender": "您对老师性别有偏好吗？如果没有要求，我会默认匹配任意合适老师。",
            "start_time": "还需要确认具体上课时间，例如周六下午3点或明天晚上7点；如果还没说明学生年级和学科，也可以一起补充。",
            "duration": "请问您希望每次课程多长时间？例如60分钟、90分钟或120分钟。",
            "project": "请问学生需要预约哪个课程或学科？例如初中数学、高中物理、英语听说或语文作文。",
            "preference": "请问学生的年级、薄弱点、学习目标、老师风格偏好，或线上/线下/上门上课偏好是什么？"
        }
    
    def create_appointment_success_message(self, tech: Dict[str, Any]) -> str:
        """创建预约成功消息"""
        # 检查是否是推荐老师
        if tech.get('is_recommendation'):
            original_tech = tech.get('original_technician', {})
            return (f"\n排课助手：已为您预约老师：{tech['name']}，性别：{tech['gender']}。试听课/课程预约成功！"
                    f"（原指定的{original_tech.get('name', '')}老师时间冲突，{tech['name']}在相近学科和教学方向上同样合适）"
                    "请提前准备学生近期作业、试卷或错题本，方便老师快速了解学习情况。\n")
        else:
            return (f"\n排课助手：已为您预约老师：{tech['name']}，性别：{tech['gender']}。试听课/课程预约成功！"
                    "请提前准备学生近期作业、试卷或错题本；如为线上课，请提前检查网络、摄像头和麦克风。\n")

    def create_technician_recommendation_message(self, original_tech: Dict[str, Any], 
                                               recommended_tech: Dict[str, Any], 
                                               appointment_history: Dict[str, Any],
                                               llm=None) -> str:
        """创建老师推荐消息，使用LLM生成个性化措辞"""
        project = appointment_history.get('project', '试听课/课程')
        start_time = appointment_history.get('start_time', '')
        
        if llm:
            try:
                # 构建LLM提示
                prompt = f"""
作为一个专业的家教课程预约和排课助手，用户想预约{original_tech['name']}老师安排{project}，但{original_tech['name']}老师在{start_time}这个时间段不空闲。

我找到了一位适合的老师：
- 姓名：{recommended_tech['name']}
- 性别：{recommended_tech['gender']}  
- 专长：{recommended_tech.get('strength', '')}

原老师专长：{original_tech.get('strength', '')}

请帮我生成一段温馨、专业的推荐话术，告诉用户原老师没空，但推荐老师在相近学科、年级或教学风格上同样合适，这个时间段有空，询问用户是否愿意预约推荐老师。

要求：
1. 语气温和、专业
2. 突出推荐老师的教学经验、学科方向或适合学生类型
3. 明确询问用户意愿
4. 字数控制在80字以内
"""
                
                response = llm.invoke(prompt)
                if hasattr(response, 'content'):
                    generated_msg = response.content.strip()
                    if generated_msg:
                        return f"\n排课助手：{generated_msg}\n"
                
            except Exception as e:
                logger.warning("LLM生成推荐消息失败: %s", e)
        
        # 如果LLM失败，使用默认消息
        return (f"\n排课助手：抱歉，{original_tech['name']}老师在{start_time}这个时间段不空闲。"
                f"不过{recommended_tech['name']}老师（{recommended_tech['gender']}）在{project}方向同样合适，"
                f"这个时间段可以上课，请问您愿意让我帮您预约{recommended_tech['name']}老师吗？\n")

    def create_recommendation_declined_message(self, llm=None) -> str:
        """创建用户拒绝推荐时的消息"""
        if llm:
            try:
                prompt = """
用户拒绝了我推荐的老师，请帮我生成一段专业、温馨的回复，表达理解并提供其他选择建议。

要求：
1. 表达理解用户的选择
2. 提供其他解决方案（如换时间、重新匹配老师、调整上课方式等）
3. 保持专业和友好的语气
4. 字数控制在60字以内
"""
                response = llm.invoke(prompt)
                if hasattr(response, 'content'):
                    generated_msg = response.content.strip()
                    if generated_msg:
                        return f"\n排课助手：{generated_msg}\n"
            except Exception as e:
                logger.warning("LLM生成拒绝消息失败: %s", e)
        
        # 默认消息
        return "\n排课助手：好的，我理解您的选择。您可以选择其他时间段，或者我可以根据学生年级、科目和老师风格偏好重新推荐老师。请问您还有其他需要吗？\n"
    
    def create_appointment_failure_message(self, technician_name: str) -> str:
        """创建预约失败消息"""
        if technician_name and technician_name != "未知":
            # 通过Services层访问数据库
            from services.appointment_service import AppointmentService
            appointment_service = AppointmentService()
            specific_tech = appointment_service.get_technician_by_name(technician_name)
            if specific_tech:
                return f"\n排课助手：抱歉，{technician_name}老师在您选择的时间段不空闲。请选择其他时间，或者我可以为您推荐其他合适老师。\n"
            else:
                return f"\n排课助手：抱歉，没有找到名为'{technician_name}'的老师。请确认老师姓名，或者我可以为您推荐其他合适老师。\n"
        else:
            return "\n排课助手：抱歉，该时间段没有合适的老师可授课，请选择其他时间或调整老师偏好。\n"
    
    def create_missing_info_questions(self, missing_info: List[str]) -> str:
        """根据缺失信息创建询问"""
        questions = [
            self.missing_info_prompts.get(field, f"请补充{self.field_labels.get(field, field)}信息")
            for field in missing_info
        ]
        return "\n" + " ".join(questions) + "\n"

    def create_student_profile_suggestions(
        self,
        missing_info: List[str],
        appointment_history: Dict[str, Any],
        profile: Dict[str, Any],
    ) -> str:
        """Create optional profile-based prompts without filling appointment fields."""
        if not profile:
            return ""

        suggestions = []
        subject = self._clean_profile_value(profile.get("subject"))
        grade = self._clean_profile_value(profile.get("grade"))
        weak_points = self._clean_profile_value(profile.get("weak_points"))
        available_time = self._clean_profile_value(profile.get("available_time"))
        teacher_style = self._clean_profile_value(profile.get("teacher_style_preference"))

        if (
            "project" in missing_info
            and not self._has_usable_value(appointment_history.get("project"))
            and subject
        ):
            student_summary = "".join(part for part in [grade, subject, weak_points] if part)
            if student_summary:
                suggestions.append(f"你之前提到孩子{student_summary}，是否预约{subject}试听课？")
            else:
                suggestions.append(f"你之前提到孩子需要{subject}，是否预约{subject}试听课？")

        if (
            "start_time" in missing_info
            and not self._has_usable_value(appointment_history.get("start_time"))
            and available_time
        ):
            suggestions.append(f"你之前偏好{available_time}上课，是否优先安排{available_time}？")

        if not self._has_usable_value(appointment_history.get("preference")) and teacher_style:
            style_label = self._teacher_style_label(teacher_style)
            suggestions.append(f"你之前偏好{style_label}老师，是否按{style_label}老师匹配？")

        if not suggestions:
            return ""
        return "\n" + " ".join(suggestions) + "\n"

    def _clean_profile_value(self, value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()

    def _has_usable_value(self, value: Any) -> bool:
        if value is None:
            return False
        text = str(value).strip()
        return bool(text and text != "未知")

    def _teacher_style_label(self, value: str) -> str:
        return value if value.endswith("型") else f"{value}型"

    def format_missing_fields(self, missing_info: List[str]) -> str:
        """将内部字段名转换为用户可读的业务字段名"""
        return "、".join(self.field_labels.get(field, field) for field in missing_info)
    
    def create_unrelated_message(self) -> str:
        """创建无关请求的消息"""
        return "[REPLY][排课助手]抱歉，我无法处理这个问题。我只能帮您处理试听课预约、正式排课、老师匹配和课程相关预约。请问您需要预约试听课或安排课程吗？\n"
    
    def create_parse_error_message(self) -> str:
        """创建解析错误消息"""
        return "[REPLY][排课助手]\n排课助手：课程预约信息解析失败，请重试。\n"
    
    def create_save_failure_message(self) -> str:
        """创建保存失败消息"""
        return "\n排课助手：抱歉，课程预约保存失败，请重试。\n"
