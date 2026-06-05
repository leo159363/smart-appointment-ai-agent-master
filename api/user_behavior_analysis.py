"""
学习需求分析API - 简化版本
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/user-behavior", tags=["学习需求分析"])
router_underscore = APIRouter(prefix="/api/user_behavior", tags=["学习需求分析"])


class UserAnalysisResponse(BaseModel):
    """学习需求分析响应；内部字段名为兼容旧版本暂时保留"""
    favorite_technician_id: Optional[int] = Field(None, description="偏好老师 ID；字段名暂时保留 favorite_technician_id")
    favorite_technician_name: Optional[str] = Field(None, description="偏好老师姓名")
    favorite_service: Optional[str] = Field(None, description="常选课程或学科；字段名暂时保留 favorite_service")
    favorite_duration: Optional[int] = Field(None, description="常用课程时长，单位分钟")
    total_appointments: int = Field(0, description="累计试听预约或正式排课次数")
    days_since_last_appointment: Optional[int] = Field(None, description="距离上次试听预约或正式排课的天数")
    should_send_reminder: bool = Field(False, description="是否建议发送学习跟进提醒")


async def get_user_analysis(user_id: str = "default_user") -> UserAnalysisResponse:
    """获取学习需求分析数据"""
    try:
        from agents.user_behavior_agent import UserBehaviorAgent
        
        agent = UserBehaviorAgent()
        analysis = agent.get_user_analysis(user_id)
        
        if not analysis:
            return UserAnalysisResponse()
        
        # 获取偏好老师姓名；内部数据访问仍沿用 technician 命名
        technician_name = None
        if analysis.get('favorite_technician_id'):
            from db import TechnicianDBRouter
            db = TechnicianDBRouter()
            tech_info = db.get_technician_by_id(analysis['favorite_technician_id'])
            if tech_info:
                technician_name = tech_info.get('name')
        
        return UserAnalysisResponse(
            favorite_technician_id=analysis.get('favorite_technician_id'),
            favorite_technician_name=technician_name,
            favorite_service=analysis.get('favorite_service'),
            favorite_duration=analysis.get('favorite_duration'),
            total_appointments=analysis.get('total_appointments', 0),
            days_since_last_appointment=analysis.get('days_since_last_appointment'),
            should_send_reminder=analysis.get('should_send_reminder', False)
        )
    except Exception as e:
        # 记录异常日志并返回空数据，而不是硬编码的假数据
        import logging
        logging.error(f"获取学习需求分析数据失败: {e}")
        return UserAnalysisResponse()


@router.get("/analysis", response_model=UserAnalysisResponse, summary="获取默认学生/家长学习需求分析")
async def get_default_user_analysis():
    """获取默认学生/家长的学习需求分析数据"""
    return await get_user_analysis("default_user")


@router.get("/dashboard_data", response_model=UserAnalysisResponse, summary="获取学习需求仪表板数据")
async def get_dashboard_data():
    """获取学习需求仪表板数据"""
    return await get_user_analysis("default_user")


@router_underscore.get("/dashboard_data", response_model=UserAnalysisResponse, summary="获取学习需求仪表板数据")
async def get_dashboard_data_underscore():
    """获取学习需求仪表板数据（下划线版本）"""
    return await get_user_analysis("default_user")


class ReminderRequest(BaseModel):
    """发送学习跟进提醒请求"""
    user_id: str = Field("default_user", description="学生/家长用户 ID")


class ReminderResponse(BaseModel):
    """学习跟进提醒消息响应"""
    message: str = Field(..., description="面向学生或家长的学习跟进消息")
    technician_available_times: Optional[list] = Field(None, description="老师可授课时间建议；字段名暂时保留 technician_available_times")


@router.post("/send-reminder", response_model=ReminderResponse, summary="生成学习跟进提醒")
async def send_reminder(request: ReminderRequest):
    """生成并返回学习跟进提醒消息"""
    try:
        from agents.user_behavior_agent import UserBehaviorAgent
        
        agent = UserBehaviorAgent()
        result = await agent.get_reminder_with_schedule(request.user_id)
        
        return ReminderResponse(
            message=result["message"],
            technician_available_times=result["technician_available_times"]
        )
        
    except Exception as e:
        import logging
        logging.error(f"生成学习跟进提醒失败: {e}")
        return ReminderResponse(
            message="您好！系统暂时无法查询老师可授课时间，请稍后再试或直接联系课程顾问安排试听课或正式排课。",
            technician_available_times=[]
        )
