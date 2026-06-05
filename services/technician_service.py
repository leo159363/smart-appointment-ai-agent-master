# utils/ai/technician_service.py

from typing import List, Dict, Any
from db.db_router import DatabaseRouter
import logging

logger = logging.getLogger(__name__)

class TechnicianService:
    """老师数据服务类 - 内部沿用 technician 命名以保持兼容"""
    
    def __init__(self):
        self.db = DatabaseRouter()
        
        # 默认老师数据；字段名沿用 technician/strength 以保持数据库和调用链兼容
        self.default_technicians = [
            {
                "name": "张伟",
                "gender": "男",
                "strength": "初中数学老师，8年教龄，耐心细致型，擅长基础巩固、几何压轴题拆解和错题复盘，讲解清晰，适合基础中等或基础薄弱的学生"
            },
            {
                "name": "王强",
                "gender": "男",
                "strength": "高中物理老师，10年教龄，应试提分型，擅长力学、电学模型归纳和高频题型训练，适合高中阶段冲刺提分的学生"
            },
            {
                "name": "李娜",
                "gender": "女", 
                "strength": "英语老师，6年教龄，耐心细致型，擅长语法、阅读理解、写作提升和初中英语听说训练，适合英语基础不稳、开口不自信的学生"
            },
            {
                "name": "赵敏",
                "gender": "女",
                "strength": "语文作文老师，9年教龄，互动鼓励型，擅长素材积累、结构训练、阅读理解和表达优化，适合作文不会写、语言组织弱的学生"
            },
            {
                "name": "刘洋",
                "gender": "男",
                "strength": "小学数学老师，5年教龄，互动鼓励型，擅长学习习惯培养、计算能力训练和数学兴趣启发，适合低年级注意力不稳定的学生"
            },
            {
                "name": "孙丽",
                "gender": "女",
                "strength": "英语口语/听力老师，7年教龄，互动鼓励型，擅长线上陪练、听力精听、口语表达和长期提升，适合英语听说困难的学生"
            },
            {
                "name": "周杰",
                "gender": "男",
                "strength": "初中化学老师，6年教龄，基础补弱型，擅长概念梳理、实验题分析和中考化学题型训练，适合化学刚入门或概念混淆的学生"
            },
            {
                "name": "吴婷",
                "gender": "女",
                "strength": "学习规划老师，8年教龄，严格督促与耐心沟通结合，擅长阶段测评、错题复盘、时间管理和学习计划制定"
            },
            {
                "name": "郑斌",
                "gender": "男",
                "strength": "高三数学老师，12年教龄，应试提分型，擅长短期提分、函数导数、数列和高频题型训练，适合高三冲刺和考前查漏补缺"
            },
            {
                "name": "何静",
                "gender": "女",
                "strength": "班主任/教务老师，6年教龄，擅长课后跟进、家长沟通、排课协调和阶段反馈，适合需要持续督促和课程协调的学生"
            }
        ]

    def initialize_default_technicians(self) -> bool:
        """初始化默认老师数据"""
        try:
            # 检查是否已有老师数据
            existing_technicians = self.db.technicians.get_all_technicians()
            
            if existing_technicians:
                logger.info(f"数据库中已有 {len(existing_technicians)} 位老师，跳过初始化")
                return True
            
            logger.info("数据库中无老师数据，开始初始化默认老师")
            
            # 添加默认老师
            for tech_data in self.default_technicians:
                try:
                    tech_id = self.db.technicians.add_technician(
                        name=tech_data['name'],
                        gender=tech_data['gender'],
                        strength=tech_data['strength']
                    )
                    logger.debug(f"添加老师: {tech_data['name']} (ID: {tech_id})")
                    
                except Exception as e:
                    logger.error(f"添加老师 {tech_data['name']} 失败: {e}")
                    return False
            
            # 验证初始化结果
            final_count = len(self.db.technicians.get_all_technicians())
            logger.info(f"老师初始化完成，共添加 {final_count} 位老师")
            return True
            
        except Exception as e:
            logger.error(f"老师初始化失败: {e}")
            return False

    def get_all_technicians(self) -> List[Dict[str, Any]]:
        """获取所有老师信息"""
        return self.db.technicians.get_all_technicians()

    def get_technician_by_name(self, name: str) -> Dict[str, Any]:
        """根据姓名获取老师信息"""
        return self.db.technicians.get_technician_by_name(name)

    def get_technician_by_id(self, technician_id: int) -> Dict[str, Any]:
        """根据ID获取老师信息"""
        return self.db.technicians.get_technician_by_id(technician_id)

    def get_technician_schedules(self, technician_id: int, date) -> List[Dict[str, Any]]:
        """获取老师指定日期的排课信息"""
        return self.db.technicians.get_technician_schedules(technician_id, date)

    def is_technician_available(self, technician_id: int, start_time, end_time) -> bool:
        """检查老师在指定时间段是否可授课"""
        return self.db.technicians.is_technician_available(technician_id, start_time, end_time)

    def add_technician(self, name: str, gender: str = None, strength: str = None) -> int:
        """添加新老师"""
        return self.db.technicians.add_technician(name, gender, strength)

    def get_technicians_count(self) -> int:
        """获取老师总数"""
        technicians = self.db.technicians.get_all_technicians()
        return len(technicians)

    def get_technician_by_id(self, technician_id: int) -> Dict[str, Any]:
        """根据ID获取老师信息"""
        return self.db.technicians.get_technician_by_id(technician_id)

    def get_technician_schedules(self, technician_id: int, date) -> List[Dict[str, Any]]:
        """获取老师指定日期的排课信息"""
        return self.db.technicians.get_technician_schedules(technician_id, date)

    def is_technician_available(self, technician_id: int, start_time, end_time) -> bool:
        """检查老师在指定时间段是否可授课"""
        return self.db.technicians.is_technician_available(technician_id, start_time, end_time)
