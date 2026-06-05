"""
简化的试听课预约与正式排课API

只保留第一版核心功能
"""
from fastapi import APIRouter, HTTPException
from .core.response_models import (
    AppointmentRequest,
    AppointmentResponse,
    DataResponse
)

router = APIRouter(prefix="/api/appointment", tags=["试听课预约与正式排课"])


@router.post("/create", response_model=DataResponse, summary="创建试听课预约或正式排课")
async def create_appointment(request: AppointmentRequest):
    """创建试听课预约或正式排课；接口路径和字段名仍保留 appointment/service_type 以保持兼容"""
    try:
        # 简化实现 - 直接导入需要的服务
        from agents.appointment_agent import AppointmentAgent
        agent = AppointmentAgent()
        result = await agent.process_appointment_request(request.dict())
        
        return DataResponse(
            message="试听课预约或正式排课创建成功",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
