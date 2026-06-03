"""
消息构建器

负责构建各种响应消息
"""

from typing import Dict, Any, List


class MessageBuilder:
    """消息构建器"""
    
    def __init__(self):
        self.missing_info_prompts = {
            "gender": "您对老师性别有偏好吗？如果没有也可以说不限。",
            "start_time": "请问您希望预约哪天、几点上试听课或正式课？",
            "duration": "请问您希望每次课程多长时间？例如60分钟、90分钟或120分钟。",
            "project": "请问学生需要预约哪个课程或学科？例如初中数学、高中物理、英语听说或语文作文。",
            "preference": "请问学生的年级、薄弱点、学习目标、老师风格偏好，或线上/线下/上门上课偏好是什么？"
        }
    
    def create_appointment_success_message(self, tech: Dict[str, Any]) -> str:
        """创建预约成功消息"""
        # 检查是否是推荐老师
        if tech.get('is_recommendation'):
            original_tech = tech.get('original_technician', {})
            return (f"\n机器人：已为您预约老师：{tech['name']}，性别：{tech['gender']}。预约成功！"
                    f"（原指定的{original_tech.get('name', '')}老师时间冲突，{tech['name']}在相近学科和教学方向上同样合适）"
                    "请提前准备学生近期作业、试卷或错题，方便老师快速了解学习情况。\n")
        else:
            return (f"\n机器人：已为您预约老师：{tech['name']}，性别：{tech['gender']}。预约成功！"
                    "请提前准备学生近期作业、试卷或错题，方便老师快速了解学习情况。\n")

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
                        return f"\n机器人：{generated_msg}\n"
                
            except Exception as e:
                print(f"LLM生成推荐消息失败: {e}")
        
        # 如果LLM失败，使用默认消息
        return (f"\n机器人：抱歉，{original_tech['name']}老师在{start_time}这个时间段不空闲。"
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
                        return f"\n机器人：{generated_msg}\n"
            except Exception as e:
                print(f"LLM生成拒绝消息失败: {e}")
        
        # 默认消息
        return "\n机器人：好的，我理解您的选择。您可以选择其他时间段，或者我可以根据学生年级、科目和老师风格偏好重新推荐老师。请问您还有其他需要吗？\n"
    
    def create_appointment_failure_message(self, technician_name: str) -> str:
        """创建预约失败消息"""
        if technician_name and technician_name != "未知":
            # 通过Services层访问数据库
            from services.appointment_service import AppointmentService
            appointment_service = AppointmentService()
            specific_tech = appointment_service.get_technician_by_name(technician_name)
            if specific_tech:
                return f"\n机器人：抱歉，{technician_name}老师在您选择的时间段不空闲。请选择其他时间，或者我可以为您推荐其他合适老师。\n"
            else:
                return f"\n机器人：抱歉，没有找到名为'{technician_name}'的老师。请确认老师姓名，或者我可以为您推荐其他合适老师。\n"
        else:
            return "\n机器人：抱歉，该时间段没有合适的老师可授课，请选择其他时间或调整老师偏好。\n"
    
    def create_missing_info_questions(self, missing_info: List[str]) -> str:
        """根据缺失信息创建询问"""
        questions = [self.missing_info_prompts.get(field, f"请补充{field}信息") for field in missing_info]
        return "\n" + " ".join(questions) + "\n"
    
    def create_unrelated_message(self) -> str:
        """创建无关请求的消息"""
        return "[REPLY][预约机器人]抱歉，我无法处理这个问题。我只能帮您处理试听课预约、正式排课、老师匹配和课程相关预约。请问您需要预约试听课或安排课程吗？\n"
    
    def create_parse_error_message(self) -> str:
        """创建解析错误消息"""
        return "[REPLY][预约机器人]\n机器人：课程预约信息解析失败，请重试。\n"
    
    def create_save_failure_message(self) -> str:
        """创建保存失败消息"""
        return "\n机器人：抱歉，课程预约保存失败，请重试。\n"
