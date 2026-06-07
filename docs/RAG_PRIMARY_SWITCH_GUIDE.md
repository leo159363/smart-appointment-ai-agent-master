# Modular RAG Primary 模式切换指南

## 1. 当前三种模式

当前项目通过 `RAG_MCP_MODE` 支持三种 RAG 模式：

- `local`：默认模式，只使用本地 SQLite + Embedding + FAISS，通过 `KnowledgeService.search()` 检索课程知识。
- `shadow`：正式回答仍使用本地 RAG，后台旁路调用 Modular RAG 做对比，并写入 jsonl 日志。
- `primary`：正式回答优先使用 Modular RAG；如果 Modular 不可用、超时、报错或返回空文档，则自动 fallback 到本地 RAG。

默认仍是 `local`，不设置环境变量时不会改变现有咨询链路。

## 2. 为什么保留 fallback

Primary 不是硬替换。本地 FAISS 必须保留为 fallback，原因包括：

- Modular 服务可能未启动。
- `tutoring_course_kb` collection 可能尚未导入。
- HTTP、stdio 或 CLI 调用可能失败。
- Modular embedding、rerank 或外部模型配置可能不可用。
- 在 RAG 质量未稳定前，不能让外部 RAG 层影响用户课程咨询。

fallback 的目标是保证用户看不到 MCP 错误，首页咨询仍能正常回答。

## 3. 启用 primary 的前置条件

启用前建议确认：

1. 已使用 `scripts/export_tutoring_kb_for_modular_rag.py` 导出当前课程知识库。
2. 已将课程知识导入 `MODULAR-RAG-MCP-SERVER-main`。
3. collection 名称为 `tutoring_course_kb`。
4. `query_knowledge_hub` 可正常返回文档。
5. Shadow 日志显示 Modular 检索结果与本地 RAG 结果质量接近或更好。

如果这些条件不满足，建议继续使用 `local` 或 `shadow`。

## 4. 环境变量配置

stdio MCP 推荐配置：

```powershell
$env:RAG_MCP_MODE="primary"
$env:RAG_MCP_TRANSPORT="mcp_stdio"
$env:RAG_MCP_COLLECTION="tutoring_course_kb"
$env:RAG_MCP_TOP_K="3"
$env:RAG_MCP_TIMEOUT_SECONDS="3"
$env:RAG_MCP_LOG_PATH="logs/rag_eval/primary_eval.jsonl"
$env:RAG_MCP_SERVER_CWD="D:\Agents\Agent-RAG-test\MODULAR-RAG-MCP-SERVER-main"
```

如果未来给 Modular RAG 包装 HTTP adapter，可使用：

```powershell
$env:RAG_MCP_MODE="primary"
$env:RAG_MCP_TRANSPORT="http"
$env:RAG_MCP_ENDPOINT="http://127.0.0.1:8001"
$env:RAG_MCP_COLLECTION="tutoring_course_kb"
```

CLI transport 可用于最小 subprocess 验证：

```powershell
$env:RAG_MCP_MODE="primary"
$env:RAG_MCP_TRANSPORT="cli"
$env:RAG_MCP_SERVER_CWD="D:\Agents\Agent-RAG-test\MODULAR-RAG-MCP-SERVER-main"
```

## 5. 启动顺序

1. 启动或准备 `MODULAR-RAG-MCP-SERVER-main`。
2. 确认 `tutoring_course_kb` collection 已导入。
3. 设置 `RAG_MCP_MODE=primary` 和对应 transport 配置。
4. 启动当前家教项目。
5. 在首页输入课程咨询问题。
6. 检查回答是否正常。
7. 查看 `logs/rag_eval/*.jsonl`，确认 `final_source` 是 `modular_primary` 或 `local_fallback`。

当前项目不会提交 `logs/`，这些日志只作为本地评估记录。

## 6. 降级策略

Primary 模式下，系统会先调用 Modular RAG。

如果 Modular 返回有效 documents：

- 将 Modular 文档转换成当前 `knowledge_docs` 结构。
- `final_source=modular_primary`。
- 正式回答使用 Modular 返回的知识片段。

如果 Modular 不可用、超时、报错、collection 不存在或返回空文档：

- 自动调用本地 `KnowledgeService.search()`。
- `final_source=local_fallback`。
- 日志记录 `fallback_reason` 和 Modular error。
- 用户不会看到 MCP 错误。

## 7. 面试表述

推荐表述：

“当前系统支持将 Modular RAG MCP Server 作为主检索源，但不是硬替换。本地 FAISS 仍作为 fallback。这样既能验证外部 RAG/MCP 层的检索效果，又能保证 Modular 服务不可用时首页咨询不受影响。”

不要表述为：

“本地 RAG 已经被完全废弃。”

