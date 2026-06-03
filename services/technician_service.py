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
                "name": "张明远",
                "gender": "男",
                "strength": "初中数学老师，8年教龄，耐心细致型，擅长数学基础补弱、分数方程、函数入门和几何证明，适合基础薄弱、做题容易卡步骤的学生"
            },
            {
                "name": "王睿",
                "gender": "男",
                "strength": "高中数学老师，10年教龄，应试提分型，擅长函数、导数、数列和高考压轴题拆解，适合目标明确、需要短期提分和题型训练的学生"
            },
            {
                "name": "李安琪",
                "gender": "女", 
                "strength": "初中英语老师，6年教龄，互动鼓励型，擅长英语听说、语法基础、阅读理解和中考口语训练，适合英语听说困难、开口不自信的学生"
            },
            {
                "name": "赵雅文",
                "gender": "女",
                "strength": "语文作文老师，9年教龄，耐心细致型，擅长作文结构、素材积累、阅读理解和表达训练，适合作文不会写、语言组织弱的学生"
            },
            {
                "name": "刘承宇",
                "gender": "男",
                "strength": "初高中物理老师，7年教龄，基础补弱型，擅长力学、电学、物理概念梳理和实验题分析，适合物理概念不清、公式不会用的学生"
            },
            {
                "name": "孙雨晴",
                "gender": "女",
                "strength": "小学数学和语文老师，5年教龄，互动鼓励型，擅长兴趣启发、基础计算、阅读表达和学习信心建立，适合低年级注意力不稳定的学生"
            },
            {
                "name": "周博",
                "gender": "男",
                "strength": "初高中理科老师，11年教龄，严格督促型，擅长学习计划执行、作业检查、错题复盘和阶段目标管理，适合需要老师督促学习习惯的学生"
            },
            {
                "name": "吴思涵",
                "gender": "女",
                "strength": "高中英语老师，8年教龄，应试提分型，擅长完形阅读、写作模板、听力训练和高考英语提分，适合考前短期冲刺的学生"
            },
            {
                "name": "郑启航",
                "gender": "男",
                "strength": "数学竞赛和拔高老师，9年教龄，擅长拔高竞赛型，擅长思维拓展、压轴题、竞赛入门和高阶题型训练，适合校内成绩较好、需要拓展拔高的学生"
            },
            {
                "name": "何静怡",
                "gender": "女",
                "strength": "学习规划老师，6年教龄，严格督促与耐心沟通结合，擅长学习习惯培养、时间管理、家校沟通和阶段反馈，适合自律性弱、需要持续跟进的学生"
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
