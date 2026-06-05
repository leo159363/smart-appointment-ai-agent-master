"""
老师管理API

提供老师信息、老师状态和老师课表查询接口。接口路径和内部字段仍沿用 technician 命名以保持兼容。
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/technicians", tags=["老师管理"])


class TechnicianResponse(BaseModel):
    """老师信息响应；内部模型名保留 TechnicianResponse"""
    id: int = Field(..., description="老师 ID；内部字段仍沿用 technician id")
    name: str = Field(..., description="老师姓名")
    gender: str = Field(..., description="老师性别")
    strength: str = Field(..., description="老师擅长科目、适合年级、教学风格和擅长方向")


class ScheduleResponse(BaseModel):
    """老师课表信息响应"""
    id: int = Field(..., description="课表记录 ID")
    technician_id: int = Field(..., description="老师 ID；字段名为兼容旧版本暂时保留 technician_id")
    start_time: str = Field(..., description="课程或可授课时段开始时间")
    end_time: str = Field(..., description="课程或可授课时段结束时间")
    status: str = Field(..., description="课表状态，例如空闲或已排课")
    appointment_id: int | None = Field(None, description="关联的试听课预约或正式排课 ID")


@router.get("/", response_model=List[TechnicianResponse], summary="获取所有老师")
async def get_all_technicians():
    """获取所有老师信息"""
    try:
        from services.technician_service import TechnicianService
        technician_service = TechnicianService()
        technician_service.initialize_default_technicians()
        technicians = technician_service.get_all_technicians()
        
        return [
            TechnicianResponse(
                id=tech["id"],
                name=tech["name"],
                gender=tech.get("gender", ""),
                strength=tech.get("strength", "")
            )
            for tech in technicians
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取老师信息失败: {str(e)}")


@router.get("/{technician_id}/schedule", response_model=List[ScheduleResponse], summary="获取老师课表")
async def get_technician_schedule(technician_id: int):
    """获取指定老师今天的课表信息；路径参数名仍保留 technician_id"""
    try:
        from services.technician_service import TechnicianService
        from config.time_config import time_config
        
        technician_service = TechnicianService()
        technician_service.initialize_default_technicians()
        
        # 获取老师信息确认存在
        tech = technician_service.get_technician_by_id(technician_id)
        if not tech:
            raise HTTPException(status_code=404, detail="老师不存在")
        
        # 获取今天的课表
        today = time_config.today()
        schedules = technician_service.get_technician_schedules(technician_id, today)
        
        return [
            ScheduleResponse(
                id=sched["id"],
                technician_id=sched["technician_id"],
                start_time=sched["start_time"].strftime("%H:%M"),
                end_time=sched["end_time"].strftime("%H:%M"),
                status=sched["status"],
                appointment_id=sched.get("appointment_id")
            )
            for sched in schedules
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取老师课表失败: {str(e)}")


@router.get("/{technician_id}", response_model=TechnicianResponse, summary="获取单个老师信息")
async def get_technician(technician_id: int):
    """获取指定老师的详细信息；路径参数名仍保留 technician_id"""
    try:
        from services.technician_service import TechnicianService
        
        technician_service = TechnicianService()
        technician_service.initialize_default_technicians()
        tech = technician_service.get_technician_by_id(technician_id)
        
        if not tech:
            raise HTTPException(status_code=404, detail="老师不存在")
        
        return TechnicianResponse(
            id=tech["id"],
            name=tech["name"],
            gender=tech.get("gender", ""),
            strength=tech.get("strength", "")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取老师信息失败: {str(e)}")


@router.get("/schedules/today", summary="获取所有老师今日课表")
async def get_all_technicians_schedule_today():
    """获取所有老师今天的课表信息"""
    try:
        from services.technician_service import TechnicianService
        from config.time_config import time_config
        
        technician_service = TechnicianService()
        technician_service.initialize_default_technicians()
        
        # 获取所有老师
        all_technicians = technician_service.get_all_technicians()
        today = time_config.today()
        
        schedules_data = []
        for tech in all_technicians:
            tech_id = tech["id"]
            tech_name = tech["name"]
            
            # 获取该老师今天的课表
            tech_schedules = technician_service.get_technician_schedules(tech_id, today)
            
            busy_periods = []
            for sched in tech_schedules:
                if sched.get("status") == "busy":
                    busy_periods.append({
                        "start": sched["start_time"].strftime("%H:%M") if hasattr(sched["start_time"], 'strftime') else str(sched["start_time"]),
                        "end": sched["end_time"].strftime("%H:%M") if hasattr(sched["end_time"], 'strftime') else str(sched["end_time"]),
                        "appointment_id": sched.get("appointment_id")
                    })
            
            schedules_data.append({
                "technician_id": tech_id,
                "technician_name": tech_name,
                "busy_periods": busy_periods
            })
        
        return schedules_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取老师课表失败: {str(e)}")
