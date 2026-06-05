"""
简化的课程咨询与排课任务分类API

只保留第一版核心功能
"""
from fastapi import APIRouter, HTTPException
from .core.response_models import (
    TaskClassificationRequest,
    TaskClassificationResponse,
    DataResponse
)

router = APIRouter(prefix="/api/task", tags=["课程任务分类"])


@router.post("/classify", response_model=DataResponse, summary="分类课程咨询与排课任务")
async def classify_task(request: TaskClassificationRequest):
    """分类课程咨询、试听课预约、正式排课、学习需求分析或无关问题"""
    try:
        # 简化实现 - 直接导入需要的agent
        from agents.task_classification_agent import TaskClassificationAgent
        agent = TaskClassificationAgent()
        result = await agent.classify_task(request.message)
        
        return DataResponse(
            message="课程咨询与排课任务分类成功",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
