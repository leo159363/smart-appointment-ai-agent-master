from agents.task_classification_agent import TaskClassificationAgent
from agents.appointment_agent import AppointmentAgent
from agents.consultant_agent import ConsultantAgent
from services.student_profile_service import StudentProfileService
import uuid

# 全局session_id用于单用户场景
global_session_id = str(uuid.uuid4())

task_agent = TaskClassificationAgent(
    AppointmentAgent(session_id=global_session_id), 
    ConsultantAgent(session_id=global_session_id)
)

async def ProcessUserInput_stream(user_input, state=None, context=None, user_id=None):
    """
    user_input: 用户输入
    state: 当前对话状态（如 None, 'classify', 'appointment', 'query', ...）
    context: 可选，保存多轮对话上下文（如 dict，可存储 agent 的 history 等）
    返回: (reply, next_state, next_context)
    """
    # 初始化 context
    if context is None:
        context = {}

    consultant_agent = getattr(task_agent, "consultant_agent", None)
    original_consultant_state = None
    if user_id is not None and consultant_agent is not None:
        original_consultant_state = {
            "user_id": getattr(consultant_agent, "user_id", "default_user"),
            "student_profile_service": getattr(consultant_agent, "_student_profile_service", None),
            "auto_update_student_profile": getattr(consultant_agent, "auto_update_student_profile", False),
            "enable_stream_student_profile_context": getattr(consultant_agent, "enable_stream_student_profile_context", False),
        }
        consultant_agent.user_id = user_id or "default_user"
        consultant_agent._student_profile_service = StudentProfileService()
        consultant_agent.auto_update_student_profile = True
        consultant_agent.enable_stream_student_profile_context = True

    try:
        async for token in task_agent.classify_task_stream(user_input):
            yield token
    finally:
        if original_consultant_state is not None:
            consultant_agent.user_id = original_consultant_state["user_id"]
            consultant_agent._student_profile_service = original_consultant_state["student_profile_service"]
            consultant_agent.auto_update_student_profile = original_consultant_state["auto_update_student_profile"]
            consultant_agent.enable_stream_student_profile_context = original_consultant_state["enable_stream_student_profile_context"]
