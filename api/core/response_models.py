"""
简化的API响应模型

只保留第一版真正需要的核心功能
"""
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
from datetime import datetime
from config.time_config import time_config


class BaseResponse(BaseModel):
    """基础响应模型"""
    message: str
    timestamp: datetime = time_config.now()


class DataResponse(BaseResponse):
    """数据响应模型"""
    data: Any


# 试听课预约/正式排课相关模型
class AppointmentRequest(BaseModel):
    user_id: str = Field(..., description="学生或家长用户 ID")
    service_type: str = Field(..., description="课程/学科；字段名为兼容旧版本暂时保留 service_type")
    preferred_time: str = Field(..., description="期望试听课或正式课时间")
    notes: Optional[str] = Field(None, description="学习需求、薄弱科目、老师风格偏好或其他排课备注")


class AppointmentResponse(BaseModel):
    appointment_id: str = Field(..., description="试听课预约或正式排课 ID")
    user_id: str = Field(..., description="学生或家长用户 ID")
    service_type: str = Field(..., description="课程/学科；字段名为兼容旧版本暂时保留 service_type")
    scheduled_time: str = Field(..., description="已安排的试听课或正式课时间")
    status: str = Field(..., description="预约或排课状态")
    notes: Optional[str] = Field(None, description="学习需求、老师偏好或排课备注")


# 课程咨询相关模型
class ConsultationRequest(BaseModel):
    user_id: str = Field("default_user", description="学生或家长用户 ID")
    question: str = Field(..., description="课程体系、收费规则、老师介绍、试听课规则或学习规划相关问题")
    category: Optional[str] = Field(None, description="可选课程知识分类")


class ConsultationResponse(BaseModel):
    consultation_id: str = Field(..., description="课程咨询记录 ID")
    question: str = Field(..., description="用户提交的课程咨询问题")
    answer: str = Field(..., description="课程咨询回答")
    category: Optional[str] = Field(None, description="课程知识分类")


# 学习需求分析相关模型
class UserBehaviorRequest(BaseModel):
    user_id: str = Field(..., description="学生或家长用户 ID")
    action: str = Field(..., description="咨询、试听预约、正式排课、反馈等行为")
    context: Optional[Dict[str, Any]] = Field(None, description="学习需求、课程偏好、老师偏好或排课上下文")


class UserBehaviorResponse(BaseModel):
    user_id: str = Field(..., description="学生或家长用户 ID")
    action: str = Field(..., description="咨询、试听预约、正式排课、反馈等行为")
    timestamp: datetime = Field(..., description="行为记录时间")
    context: Optional[Dict[str, Any]] = Field(None, description="学习需求、课程偏好、老师偏好或排课上下文")


# 课程咨询与排课任务分类相关模型
class TaskClassificationRequest(BaseModel):
    text: str = Field(..., description="待分类的用户输入")
    context: Optional[Dict[str, Any]] = Field(None, description="对话上下文或业务上下文")


class TaskClassificationResponse(BaseModel):
    text: str = Field(..., description="原始用户输入")
    category: str = Field(..., description="任务类别，例如课程咨询、试听课预约、正式排课或学习需求分析")
    confidence: float = Field(..., description="分类置信度")
    reasoning: Optional[str] = Field(None, description="分类理由")
