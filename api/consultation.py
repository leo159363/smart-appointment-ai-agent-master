"""
简化的课程咨询API

只保留第一版核心功能
"""
from fastapi import APIRouter, HTTPException
from .core.response_models import (
    ConsultationRequest,
    DataResponse
)
from agents.consultant_agent import ConsultantAgent
from services.student_profile_service import StudentProfileService

router = APIRouter(prefix="/api/consultation", tags=["课程咨询"])


@router.post("/ask", response_model=DataResponse, summary="提交课程咨询问题")
async def ask_consultation(request: ConsultationRequest):
    """提交课程体系、收费规则、老师介绍、试听课规则或学习规划相关咨询问题"""
    try:
        user_id = request.user_id or "default_user"
        student_profile_service = StudentProfileService()
        profile_data = student_profile_service.extract_profile_from_text(request.question)
        if profile_data:
            student_profile_service.update_profile(user_id, profile_data, source="consultation_api")

        agent = ConsultantAgent(
            user_id=user_id,
            student_profile_service=student_profile_service,
        )
        result = await agent.consult(request.question)
        
        return DataResponse(
            message="课程咨询处理成功",
            data={"answer": result, "question": request.question}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
