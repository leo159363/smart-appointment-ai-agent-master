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
                "content": "我们的咨询时间为每天 9:00-22:00，正式上课时间可根据学生和老师时间灵活排课。工作日晚上、周末白天、寒暑假时段都可以预约课程顾问沟通。",
                "category": "咨询/上课时间",
                "keywords": ["咨询时间", "上课时间", "排课", "周末", "寒暑假"]
            },
            {
                "content": "我们提供小学、初中、高中数学、英语、语文作文、物理、化学等一对一课程，也支持基础补弱、考前短期提分、作文专项、英语听说和学习习惯督促。",
                "category": "课程体系",
                "keywords": ["课程体系", "一对一", "数学", "英语", "语文作文", "物理", "化学", "基础补弱"]
            },
            {
                "content": "老师均具备学科教学经验，可根据学生基础、目标分数和学习习惯匹配授课风格。常见风格包括耐心细致型、应试提分型、互动鼓励型、严格督促型、基础补弱型和拔高竞赛型。",
                "category": "老师介绍",
                "keywords": ["老师介绍", "教学经验", "教学风格", "耐心细致", "应试提分", "基础补弱", "拔高竞赛"]
            },
            {
                "content": "支持线下校区上课和线上直播课，具体方式可在试听课前确认。线下课程会根据校区距离和老师课表安排，上门授课需单独确认覆盖范围和时间。",
                "category": "校区/线上课",
                "keywords": ["校区", "线上课", "直播课", "线下课", "上门授课", "上课地点"]
            },
            {
                "content": "试听课后会根据学生表现生成学习建议，并推荐正式课排课方案。正式课程会围绕学生薄弱点、目标分数、阶段测评和错题复盘持续调整。",
                "category": "课程介绍",
                "keywords": ["试听课", "正式课", "学习建议", "薄弱点", "目标分数", "错题复盘"]
            },
            {
                "content": "教学质量通过课堂反馈、阶段测评、错题复盘和家长回访进行跟踪。课程顾问会结合老师反馈和学生作业情况，建议是否调整频次、老师或学习计划。",
                "category": "教学质量",
                "keywords": ["教学质量", "课堂反馈", "阶段测评", "错题复盘", "家长回访", "学习计划"]
            },
            {
                "content": "试听课可提前预约；正式课程需要确认学生时间、老师时间和课程包。改约、请假和补课通常需要提前联系课程顾问，排课时会避免与老师已有课表冲突。",
                "category": "试听/排课规则",
                "keywords": ["试听课", "正式排课", "改约", "请假", "补课", "排课冲突", "课程顾问"]
            },
            {
                "content": "我们提供试听课、10课时包、20课时包等方案。正式课程费用通常会根据学生年级、学科难度、课程类型、老师资历和课时长度综合确认。10课时包适合短期补弱或阶段冲刺，20课时包适合系统提升和长期规划。试听课后，老师会结合学生基础和学习目标给出正式课程建议，教务老师再确认具体价格和排课方案。退费需要核对剩余课时、已上课时、赠送课时、课程有效期和合同约定。",
                "category": "课时包/课程包",
                "keywords": ["课时包", "课程包", "收费", "价格", "费用", "试听课", "10课时包", "20课时包", "退费", "剩余课时", "合同"]
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
