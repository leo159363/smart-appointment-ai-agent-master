"""
任务分类器 - 专门负责判断用户请求的类型

职责：
1. 接收用户输入，分析其意图
2. 根据预定义的分类规则，将任务归类为：
   - appointment（预约任务）
   - query（查询任务）  
   - pay（支付任务）
   - statistics（统计任务）
   - other（其他任务）
3. 提供清晰的分类结果和置信度
"""

from langchain.prompts import PromptTemplate
from langchain_core.language_models.chat_models import BaseChatModel
from typing import Dict, Any


class TaskClassifier:
    """任务分类器 - 使用LLM进行智能任务分类"""
    
    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        self._initialize_prompt()
        self.chain = self.prompt | self.llm
    
    def _initialize_prompt(self):
        """初始化分类提示词模板"""
        self.prompt = PromptTemplate(
            input_variables=["task"],
            template=(
                "你是一个家教培训机构智能咨询与排课系统的任务分类助手，你会处理来自学生、家长、课程顾问和老师的消息，你的任务是对本次任务进行分类。\n"
                "用户可能会咨询课程体系、适合年级、老师介绍、老师教学风格、价格、课时包、试听课规则、退费规则、校区地址、线上课安排、家长沟通和课后反馈等，这类任务归类为查询任务。\n"
                "用户可能会请求试听课预约、正式排课、改约、请假、补课、老师匹配或确认某个上课时间，比如'请帮我预约周六下午的初中数学试听课'、'想每周三晚上固定上课'，这类任务归类为预约任务。\n"
                "appointment机器人也可能发来任务，告知用户选择了某位老师、某门课程或某个课时包，后续需要确认支付或购买课时，这类任务归类为支付任务。\n"
                "课程顾问或老师可能会发来任务，比如告知某个学生需要调整课程时间、延长课时或安排补课，这类任务归类为预约任务。\n"
                "课程顾问或老师也可能告知已完成试听课、正式课或阶段反馈，这类任务归类为统计任务。\n"
                "如果输入的任务与上述都无关，请归类为其它任务。\n"
                "请将以下任务归类为以下类别，输出只能选择以下之一：\n"
                "1. appointment（预约任务）\n"
                "2. query（查询任务）\n"
                "3. pay（支付任务）\n"
                "4. statistics（统计任务）\n"
                "5. other（其它任务）\n"
                "只返回类别英文名。\n\n"
                "举例说明：假如task为'我想预约周六下午的初中英语试听课'，则输出appointment。\n"
                "假如task为'帮我安排每周三晚上的高中物理正式课'，则输出appointment。\n"
                "假如task为'孩子数学基础薄弱，帮我匹配一位耐心的老师'，则输出appointment。\n"
                "假如task为'初中数学一对一怎么收费'，则输出query。\n"
                "假如task为'你们有哪些老师，适合几年级'，则输出query。\n"
                "假如task为'可以线上上课吗，校区在哪里'，则输出query。\n"
                "假如task为'我要购买20课时包'，则输出pay。\n"
                "假如task为'张老师今天的试听课已经完成'，则输出statistics。\n"
                "以下是本次归类任务:\n"
                "任务内容：{task}"
            )
        )
    
    async def classify_task(self, task: str) -> str:
        """
        分类任务
        
        Args:
            task: 用户输入的任务内容
            
        Returns:
            str: 分类结果 ('appointment', 'query', 'pay', 'statistics', 'other')
        """
        try:
            category_msg = await self.chain.ainvoke({"task": task})
            category = category_msg.content.strip().lower()
            
            # 验证分类结果是否有效
            valid_categories = {'appointment', 'query', 'pay', 'statistics', 'other'}
            if category not in valid_categories:
                return 'other'  # 默认归类为其他
                
            return category
            
        except Exception as e:
            print(f"任务分类失败: {str(e)}")
            return 'other'  # 发生错误时默认归类为其他
    
    def get_category_description(self, category: str) -> str:
        """获取分类类别的描述信息"""
        descriptions = {
            'appointment': '预约任务 - 试听课预约、正式排课、老师匹配、改约请假补课等请求',
            'query': '查询任务 - 课程体系、老师介绍、收费课时包、校区线上课、学习规划等咨询',
            'pay': '支付任务 - 课时包购买、试听课或正式课确认后的支付相关事务',
            'statistics': '统计任务 - 课程顾问或老师上报试听课、正式课、阶段反馈完成状态',
            'other': '其他任务 - 与家教课程咨询和排课无关的请求'
        }
        return descriptions.get(category, '未知任务类型')
