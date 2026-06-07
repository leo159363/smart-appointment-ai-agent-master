"""
知识检索器

负责从知识库中检索相关信息
"""

import asyncio
from typing import List, Dict, Any
from services.knowledge_service import KnowledgeService
from config.rag_mcp_config import load_rag_mcp_config
from services.rag_mcp_client import RagMcpClient
from services.rag_eval_logger import RagEvalLogger


class KnowledgeRetriever:
    """知识检索器"""
    
    def __init__(self):
        self.knowledge_service = KnowledgeService()
        self.kb_initialized = False
        self.rag_mcp_config = load_rag_mcp_config()
        self.rag_mcp_client = RagMcpClient(self.rag_mcp_config)
        self.rag_eval_logger = RagEvalLogger(self.rag_mcp_config)
    
    async def initialize(self):
        """初始化知识库服务"""
        if not self.kb_initialized:
            await self.knowledge_service.initialize()
            self.kb_initialized = True
            print("✅ 咨询机器人知识库服务已初始化")
    
    async def search_knowledge(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """搜索相关知识"""
        if self.rag_mcp_config.is_primary:
            return await self._search_primary(query, top_k)

        relevant_docs = await self._search_local(query, top_k)
        self._schedule_shadow_eval(query, relevant_docs, top_k)
        return relevant_docs

    async def _search_local(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """执行本地 KnowledgeService.search()。"""
        if not self.kb_initialized:
            await self.initialize()

        relevant_docs = await self.knowledge_service.search(query, top_k=top_k)
        self._log_search_results(query, relevant_docs)
        return relevant_docs or []

    async def _search_primary(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Primary 模式：优先 Modular RAG，失败时 fallback 本地 RAG。"""
        modular_top_k = self.rag_mcp_config.top_k or top_k
        modular_result = await self._query_modular(query, modular_top_k)
        modular_docs = modular_result.get("documents", [])

        if modular_result.get("ok") and modular_docs:
            knowledge_docs = self._convert_modular_documents_to_knowledge_docs(modular_docs)
            if knowledge_docs:
                self.rag_eval_logger.log_primary(
                    query=query,
                    local_documents=None,
                    modular_result=modular_result,
                    local_top_k=top_k,
                    modular_top_k=modular_top_k,
                    event="primary_used_modular",
                    final_source="modular_primary",
                )
                self._log_search_results(query, knowledge_docs)
                return knowledge_docs

        local_docs = await self._search_local(query, top_k)
        fallback_reason = "primary_modular_empty" if modular_result.get("ok") else "primary_modular_error"
        self.rag_eval_logger.log_primary(
            query=query,
            local_documents=local_docs,
            modular_result=modular_result,
            local_top_k=top_k,
            modular_top_k=modular_top_k,
            event="primary_fallback_local",
            final_source="local_fallback",
            fallback_reason=fallback_reason,
        )
        return local_docs

    async def _query_modular(self, query: str, top_k: int) -> Dict[str, Any]:
        """调用 Modular RAG，异常统一转成失败结果。"""
        try:
            return await asyncio.to_thread(
                self.rag_mcp_client.query,
                query,
                top_k,
                self.rag_mcp_config.collection,
            )
        except Exception as error:
            return {
                "ok": False,
                "query": query,
                "collection": self.rag_mcp_config.collection,
                "documents": [],
                "latency_ms": 0,
                "error": str(error),
            }

    def _convert_modular_documents_to_knowledge_docs(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """将 Modular RAG 文档转换为 PromptBuilder 兼容的 knowledge_docs。"""
        knowledge_docs = []
        for index, document in enumerate(documents, start=1):
            content = str(document.get("content") or "").strip()
            if not content:
                continue

            try:
                score = float(document.get("score", 0) or 0)
            except (TypeError, ValueError):
                score = 0.0

            try:
                rank = int(document.get("rank") or index)
            except (TypeError, ValueError):
                rank = index

            knowledge_docs.append(
                {
                    "id": f"modular_{rank}",
                    "content": content,
                    "category": document.get("category") or "课程知识",
                    "keywords": [],
                    "score": score,
                    "rank": rank,
                    "source": "modular_rag_mcp",
                }
            )
        return knowledge_docs

    def _schedule_shadow_eval(self, query: str, local_docs: List[Dict[str, Any]], local_top_k: int):
        """旁路触发 Modular RAG Shadow 对比，不影响正式返回。"""
        if not self.rag_mcp_config.is_shadow:
            return

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._run_shadow_eval(query, local_docs, local_top_k))
        except RuntimeError:
            return

    async def _run_shadow_eval(self, query: str, local_docs: List[Dict[str, Any]], local_top_k: int):
        """后台调用 Modular RAG 并写对比日志。"""
        modular_top_k = self.rag_mcp_config.top_k or local_top_k
        try:
            modular_result = await asyncio.to_thread(
                self.rag_mcp_client.query,
                query,
                modular_top_k,
                self.rag_mcp_config.collection,
            )
        except Exception as error:
            modular_result = {
                "ok": False,
                "query": query,
                "collection": self.rag_mcp_config.collection,
                "documents": [],
                "latency_ms": 0,
                "error": str(error),
            }

        self.rag_eval_logger.log_shadow(
            query=query,
            local_documents=local_docs,
            modular_result=modular_result,
            local_top_k=local_top_k,
            modular_top_k=modular_top_k,
        )
    
    def _log_search_results(self, query: str, relevant_docs: List[Dict[str, Any]]):
        """记录搜索结果日志"""
        if relevant_docs:
            print(f"🔍 知识库检索结果 (查询: '{query}'):")
            for i, doc in enumerate(relevant_docs, 1):
                score = doc.get('score', 0)
                category = doc.get('category', '未知')
                content = doc.get('content', '')[:80]
                print(f"  {i}. [相关度:{score:.3f}] [分类:{category}] {content}...")
            print(f"📊 知识库统计: 共检索到 {len(relevant_docs)} 条相关知识")
        else:
            print(f"⚠️ 知识库检索: 未找到与 '{query}' 相关的知识")
