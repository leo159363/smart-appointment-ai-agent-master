"""
Repositories Module

数据访问对象模块，包含：
- 老师数据仓库（类名 Technician 为兼容保留）
- 知识库数据仓库  
- 用户行为数据仓库
"""

from .technician_repository import TechnicianRepository
from .knowledge_repository import KnowledgeRepository
from .user_behavior_repository import UserBehaviorRepository

__all__ = [
    'TechnicianRepository',
    'KnowledgeRepository',
    'UserBehaviorRepository'
]
