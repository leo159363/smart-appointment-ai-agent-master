"""
无关请求处理器 - 专门负责处理与业务无关的用户请求

职责：
1. 识别和处理与家教课程咨询和排课业务无关的请求
2. 提供友好的拒绝回复
3. 引导用户回到正确的业务轨道
4. 重置对话状态，准备处理下一个请求
"""

from typing import AsyncGenerator
from .state_manager import StateManager


class UnrelatedHandler:
    """无关请求处理器 - 处理与业务无关的用户请求"""
    
    def __init__(self, state_manager: StateManager):
        """
        初始化无关请求处理器
        
        Args:
            state_manager: 状态管理器
        """
        self.state_manager = state_manager
        self._default_replies = [
            "抱歉，我无法处理这个问题。我可以帮助你了解课程体系、老师介绍、试听课预约、正式排课、收费规则和学习规划等问题。",
            "很抱歉，我专门负责家教培训机构的课程咨询与排课。如果你想了解课程、老师、课时包或预约试听课，我很乐意继续帮你。",
            "对不起，这个问题超出了我的服务范围。我主要协助处理课程咨询、老师匹配、试听课预约、正式排课和学习需求分析。"
        ]
        self._reply_index = 0
    
    async def handle_unrelated_sync(self, user_input: str) -> str:
        """
        同步处理无关请求（返回字符串）
        
        Args:
            user_input: 用户输入内容
            
        Returns:
            str: 处理结果
        """
        print("归类机器人接管处理 unrelated user_input")
        
        # 重置状态为分类状态，准备处理下一个输入
        self.state_manager.reset_to_classify()
        
        # 返回友好的拒绝回复
        return self._get_next_reply()
    
    async def handle_unrelated_async(self, user_input: str) -> AsyncGenerator[str, None]:
        """
        异步处理无关请求（返回流式响应）
        
        Args:
            user_input: 用户输入内容
            
        Yields:
            str: 流式响应内容
        """
        print("归类机器人接管处理 unrelated user_input (async stream)")
        
        # 重置状态为分类状态
        self.state_manager.reset_to_classify()
        
        # 生成流式回复
        reply = self._get_next_reply()
        yield "[REPLY][归类机器人]"
        for char in reply:
            yield char
    
    def _get_next_reply(self) -> str:
        """获取下一个回复内容（轮换使用不同回复）"""
        reply = self._default_replies[self._reply_index]
        self._reply_index = (self._reply_index + 1) % len(self._default_replies)
        return reply
    
    def add_custom_reply(self, reply: str) -> None:
        """添加自定义回复"""
        if reply and reply not in self._default_replies:
            self._default_replies.append(reply)
    
    def set_business_context(self, service_name: str = "家教课程咨询与排课服务") -> None:
        """设置业务上下文，自定义回复中的服务名称"""
        self._default_replies = [
            f"抱歉，我无法处理这个问题。我只能帮你处理{service_name}相关的咨询、试听预约和排课问题。",
            f"很抱歉，我专门负责{service_name}。如果你想了解课程、老师、课时包或学习规划，我很乐意为你提供帮助。",
            f"对不起，这个问题超出了我的服务范围。我主要协助处理{service_name}，包括课程咨询、老师匹配和预约排课。"
        ]
    
    def get_available_replies(self) -> list:
        """获取所有可用的回复模板"""
        return self._default_replies.copy()
    
    def reset_reply_rotation(self) -> None:
        """重置回复轮换索引"""
        self._reply_index = 0
