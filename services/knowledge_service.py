# services/knowledge_service.py

import numpy as np
import faiss
from typing import List, Dict, Tuple, Optional
from db.db_router import DatabaseRouter
from .text_embedding import embed_input
import logging

logger = logging.getLogger(__name__)

class KnowledgeService:
    """知识库服务类 - 结合数据库存储和向量检索"""
    
    def __init__(self, db_path: str = 'sqlite:///data/smart_appointment.db'):
        # 使用统一的DatabaseRouter，符合架构设计
        self.db_router = DatabaseRouter(db_path)
        self.db = self.db_router.knowledge  # 通过router访问knowledge repository
        self.index = None
        self.document_ids = []  # 维护文档ID与索引位置的映射
        self.initialized = False
        
        # 默认家教培训知识库内容
        self.default_knowledge = [
            {
                "content": "我们的家教培训机构提供小学、初中、高中一对一辅导，覆盖数学、英语、语文作文、物理、化学等学科。课程会先通过学习需求沟通和试听课了解学生基础，再制定个性化学习方案。",
                "category": "课程体系",
                "keywords": ["课程体系", "一对一", "小学", "初中", "高中", "数学", "英语", "语文", "物理", "化学"]
            },
            {
                "content": "常见课程方向包括数学基础补弱、初中英语听说、语文作文提升、初高中物理概念梳理、考前短期提分和学习习惯督促。课程顾问会根据学生年级、薄弱科目、目标分数和可上课时间推荐合适方案。",
                "category": "课程体系",
                "keywords": ["数学基础", "英语听说", "作文", "物理", "考前提分", "学习习惯", "薄弱科目"]
            },
            {
                "content": "收费通常根据年级、科目、老师资历、课时长度和课程形式确定。试听课可单独预约，正式课一般按课时包或阶段课程购买，具体价格以课程顾问确认的方案为准。",
                "category": "收费规则",
                "keywords": ["收费", "价格", "多少钱", "课时包", "试听课", "正式课", "老师资历"]
            },
            {
                "content": "老师团队覆盖耐心细致型、应试提分型、互动鼓励型、严格督促型、基础补弱型和拔高竞赛型。匹配老师时会综合学生基础、学习目标、性格特点、沟通方式和家长偏好。",
                "category": "老师介绍",
                "keywords": ["老师", "教学风格", "耐心细致", "应试提分", "互动鼓励", "严格督促", "基础补弱", "拔高竞赛"]
            },
            {
                "content": "试听课预约需要提供学生年级、目标科目、当前学习问题、期望上课时间、上课方式和老师风格偏好。试听课通常用于诊断基础、体验老师风格并确认后续课程方案。",
                "category": "试听课规则",
                "keywords": ["试听课", "预约", "学生年级", "薄弱科目", "上课时间", "老师风格", "学习诊断"]
            },
            {
                "content": "正式排课会在试听反馈和家长确认后进行。排课时需要确认固定上课周期、每次课时长、老师可授课时间、学生可上课时间和阶段学习目标，避免与老师已有课表冲突。",
                "category": "正式排课规则",
                "keywords": ["正式排课", "固定上课", "老师课表", "可授课时间", "排课冲突", "学习目标"]
            },
            {
                "content": "如需改约或请假，请尽量提前至少24小时联系课程顾问。符合规则的请假可安排补课；临时缺席、频繁改约或超过有效期的课时，可能按机构排课和退费规则处理。",
                "category": "改约请假补课规则",
                "keywords": ["改约", "请假", "补课", "临时缺席", "课程顾问", "有效期"]
            },
            {
                "content": "退费规则通常与课时包、已上课时、赠送课时、课程有效期和合同约定有关。家长申请退费时，需要先核对剩余课时、优惠抵扣和已产生的教学服务费用。",
                "category": "退费规则",
                "keywords": ["退费", "剩余课时", "课时包", "赠送课时", "合同", "有效期"]
            },
            {
                "content": "上课前建议学生准备近期试卷、作业、错题本、教材版本和学习目标。线上课需要提前测试设备、网络、摄像头和麦克风；线下课需要按约定时间到达校区或上课地点。",
                "category": "上课须知",
                "keywords": ["上课须知", "课前准备", "试卷", "错题本", "教材", "线上课", "线下课"]
            },
            {
                "content": "课程结束后，老师或课程顾问会根据机构规则向家长反馈课堂表现、知识掌握情况、作业完成建议和下一阶段学习重点。阶段性课程可结合测评结果调整老师、频次或学习计划。",
                "category": "家长沟通和课后反馈",
                "keywords": ["家长沟通", "课后反馈", "课堂表现", "作业", "阶段测评", "学习计划"]
            }
        ]

    async def initialize(self):
        """初始化知识库服务"""
        try:
            # 检查数据库中是否已有数据
            existing_docs = self.db.get_all_documents()
            
            if not existing_docs:
                logger.info("数据库为空，初始化默认知识库")
                await self._create_default_knowledge()
            else:
                logger.info(f"从数据库加载了 {len(existing_docs)} 条知识")
            
            # 构建向量索引
            await self._build_vector_index()
            self.initialized = True
            logger.info("知识库服务初始化完成")
            
        except Exception as e:
            logger.error(f"知识库服务初始化失败: {e}")
            raise

    async def _create_default_knowledge(self):
        """创建默认知识库"""
        for knowledge in self.default_knowledge:
            try:
                # 生成嵌入向量
                text_for_embedding = f"{knowledge['content']} {' '.join(knowledge['keywords'])}"
                embedding = embed_input(text_for_embedding)
                
                # 保存到数据库
                self.db.add_document(
                    content=knowledge['content'],
                    category=knowledge['category'],
                    keywords=knowledge['keywords'],
                    embedding=embedding
                )
                logger.debug(f"添加默认知识: {knowledge['content'][:50]}...")
                
            except Exception as e:
                logger.error(f"添加默认知识失败: {e}")

    async def _build_vector_index(self):
        """构建向量索引"""
        try:
            documents = self.db.get_all_documents()
            if not documents:
                logger.warning("没有文档可用于构建索引")
                return

            embeddings = []
            self.document_ids = []
            
            for doc in documents:
                if doc.get('embedding'):
                    embeddings.append(doc['embedding'])
                    self.document_ids.append(doc['id'])
                else:
                    # 如果没有嵌入向量，生成一个
                    logger.warning(f"文档 {doc['id']} 缺少嵌入向量，正在生成...")
                    text_for_embedding = f"{doc['content']} {' '.join(doc.get('keywords', []))}"
                    embedding = embed_input(text_for_embedding)
                    
                    # 更新数据库
                    self.db.update_document(doc['id'], embedding=embedding)
                    
                    embeddings.append(embedding)
                    self.document_ids.append(doc['id'])

            if embeddings:
                # 创建FAISS索引
                embeddings_array = np.array(embeddings).astype('float32')
                dimension = embeddings_array.shape[1]
                self.index = faiss.IndexFlatIP(dimension)  # 内积相似度
                self.index.add(embeddings_array)
                logger.info(f"构建向量索引完成，包含 {len(embeddings)} 个向量")
            else:
                logger.warning("没有有效的嵌入向量，无法构建索引")

        except Exception as e:
            logger.error(f"构建向量索引失败: {e}")
            raise

    async def search(self, query: str, top_k: int = 3, category: str = None) -> List[Dict]:
        """搜索相关文档"""
        if not self.initialized or self.index is None:
            logger.warning("知识库服务未初始化或索引不可用")
            return []

        try:
            # 生成查询的嵌入向量
            query_embedding = embed_input(query)
            query_array = np.array([query_embedding]).astype('float32')
            
            # 向量搜索
            scores, indices = self.index.search(query_array, min(top_k * 2, len(self.document_ids)))  # 多检索一些候选
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.document_ids):
                    doc_id = self.document_ids[idx]
                    doc = self.db.get_document(doc_id)
                    
                    if doc:
                        # 如果指定了分类过滤
                        if category and doc.get('category') != category:
                            continue
                            
                        doc['score'] = float(score)
                        doc['rank'] = len(results) + 1
                        results.append(doc)
                        
                        # 达到所需数量就停止
                        if len(results) >= top_k:
                            break
            
            return results
            
        except Exception as e:
            logger.error(f"搜索知识库失败: {e}")
            return []

    async def add_document(self, content: str, category: str, keywords: List[str] = None) -> bool:
        """添加新文档"""
        try:
            if keywords is None:
                keywords = []
            
            # 生成嵌入向量
            text_for_embedding = f"{content} {' '.join(keywords)}"
            embedding = embed_input(text_for_embedding)
            
            # 保存到数据库
            doc_id = self.db.add_document(content, category, keywords, embedding)
            
            # 重建索引
            await self._build_vector_index()
            
            logger.info(f"成功添加文档 {doc_id}: {content[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            return False

    async def update_document(self, doc_id: int, content: str = None, category: str = None, keywords: List[str] = None) -> bool:
        """更新文档"""
        try:
            # 如果更新了内容或关键词，需要重新生成嵌入向量
            embedding = None
            if content is not None or keywords is not None:
                # 获取当前文档信息
                current_doc = self.db.get_document(doc_id)
                if not current_doc:
                    return False
                
                # 使用新值或保持原值
                final_content = content if content is not None else current_doc['content']
                final_keywords = keywords if keywords is not None else current_doc.get('keywords', [])
                
                # 生成新的嵌入向量
                text_for_embedding = f"{final_content} {' '.join(final_keywords)}"
                embedding = embed_input(text_for_embedding)
            
            # 更新数据库
            success = self.db.update_document(doc_id, content, category, keywords, embedding)
            
            if success and embedding is not None:
                # 重建索引
                await self._build_vector_index()
            
            return success
            
        except Exception as e:
            logger.error(f"更新文档失败: {e}")
            return False

    async def delete_document(self, doc_id: int, soft_delete: bool = True) -> bool:
        """删除文档"""
        try:
            success = self.db.delete_document(doc_id, soft_delete)
            
            if success:
                # 重建索引
                await self._build_vector_index()
            
            return success
            
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False

    def get_all_documents(self, include_inactive: bool = False) -> List[Dict]:
        """获取所有文档"""
        return self.db.get_all_documents(include_inactive)

    def get_document(self, doc_id: int) -> Dict:
        """获取指定文档"""
        return self.db.get_document(doc_id)

    def get_all_categories(self) -> List[str]:
        """获取所有分类"""
        return self.db.get_all_categories()

    def get_documents_count(self) -> int:
        """获取文档总数"""
        return self.db.get_documents_count()

    def search_by_category(self, category: str) -> List[Dict]:
        """按分类搜索文档"""
        return self.db.search_documents_by_category(category)

    def search_by_keywords(self, keywords: List[str]) -> List[Dict]:
        """按关键词搜索文档"""
        return self.db.search_documents_by_keywords(keywords)
