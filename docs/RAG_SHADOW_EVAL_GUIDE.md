# RAG/MCP Shadow 对比模式说明

## 1. 当前项目本地 RAG 链路

当前家教项目正式咨询回答默认优先使用 Modular RAG MCP（primary 模式），本地保留两重链路作为 fallback：

```text
默认 Primary 链路:
  Modular RAG MCP Server (query_knowledge_hub)
    -> 成功: 返回 Modular 检索结果
    -> 失败/超时/空结果: fallback 到本地

本地 fallback 链路:
  SQLite knowledge_documents
    -> Embedding
    -> FAISS
    -> KnowledgeService.search()
    -> agents/consultant/knowledge_retriever.py
  -> 咨询回答生成
```

Shadow 模式不会替换 `KnowledgeService.search()`，也不会改变首页咨询、预约、老师匹配或学习需求分析的正式用户回答。

## 2. MODULAR-RAG-MCP-SERVER 的定位

`MODULAR-RAG-MCP-SERVER-main` 当前作为独立 RAG/MCP 知识层和评估层接入候选。它实际提供：

- stdio MCP server：`python -m src.mcp_server.server`
- MCP tool：`query_knowledge_hub`
- CLI 查询脚本：`python scripts/query.py --query "..."`
- hybrid search、rerank、trace 和 collection 配置能力

当前没有确认到可直接调用的 HTTP 查询服务。因此本项目的 Shadow client 支持：

- `http`：调用外部 HTTP adapter，默认 endpoint 为 `http://127.0.0.1:8001/query_knowledge_hub`。
- `mcp_stdio`：通过 subprocess 启动 Modular MCP stdio server，并调用 `query_knowledge_hub`。
- `cli`：通过 subprocess 调用 Modular 的 `scripts/query.py`。

## 3. 为什么先做 Shadow，不直接 Primary

本地 RAG 已经支撑当前 MVP 的咨询回答。直接替换主链路会影响咨询 Agent、PromptBuilder、接口返回结构和页面演示稳定性。

Shadow 模式可以在不影响用户正式回答的前提下，对比本地 RAG 与 Modular RAG 的检索结果、耗时和错误情况。因此项目先完成 Eval-only 和 Shadow，再进入 Primary 主检索层接入；即使启用 Primary，也继续保留本地 FAISS fallback。

## 4. 配置项说明

当前默认配置如下：

```text
RAG_MCP_MODE=primary
RAG_MCP_TRANSPORT=mcp_stdio
RAG_MCP_ENDPOINT=http://127.0.0.1:8001
RAG_MCP_COLLECTION=tutoring_course_kb
RAG_MCP_TIMEOUT_SECONDS=3
RAG_MCP_TOP_K=3
RAG_MCP_LOG_PATH=logs/rag_eval/primary_eval.jsonl
```

扩展配置：

```text
RAG_MCP_TRANSPORT=http
RAG_MCP_HTTP_PATH=/query_knowledge_hub
RAG_MCP_SERVER_CWD=../MODULAR-RAG-MCP-SERVER-main
RAG_MCP_PYTHON=python
RAG_MCP_COMMAND=
```

模式说明：

- `RAG_MCP_MODE=local`：只使用当前本地 RAG，不调用 Modular。
- `RAG_MCP_MODE=shadow`：正式回答仍使用本地 RAG，后台旁路调用 Modular 并写 jsonl 日志。
- `RAG_MCP_MODE=primary`：默认模式，优先调用 Modular RAG，失败时回退本地 FAISS。

transport 说明：

- `http`：适合未来给 Modular 包一层 HTTP adapter 后调用。
- `mcp_stdio`：适合直接调用 Modular 的 stdio MCP server。
- `cli`：适合用 Modular 的 `scripts/query.py` 做最小 subprocess 查询。

## 5. 启动方式

本地项目启动：

```powershell
.\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
```

启用 Shadow 模式示例：

```powershell
$env:RAG_MCP_MODE="shadow"
$env:RAG_MCP_TRANSPORT="mcp_stdio"
$env:RAG_MCP_SERVER_CWD="D:\Agents\Agent-RAG-test\MODULAR-RAG-MCP-SERVER-main"
$env:RAG_MCP_COLLECTION="tutoring_course_kb"
```

如果使用 HTTP adapter：

```powershell
$env:RAG_MCP_MODE="shadow"
$env:RAG_MCP_TRANSPORT="http"
$env:RAG_MCP_ENDPOINT="http://127.0.0.1:8001"
```

注意：当前仓库不提交 `.env`，也不要求 Shadow 模式使用真实 API key。Modular 服务本身如需 embedding 或 rerank 外部服务，应由 Modular 项目自己的配置处理。

## 6. 测试方式

1. 打开首页：`http://127.0.0.1:8000/`
2. 输入课程咨询问题，例如：
   - 试听课、10课时包和20课时包有什么区别？
   - 初二数学基础弱，想找耐心一点的老师。
   - 高一物理力学听不懂，能不能安排冲刺课？
3. 页面正式回答仍来自本地 RAG。
4. 查看 Shadow 日志：

```powershell
Get-Content logs/rag_eval/shadow_eval.jsonl -Tail 5
```

日志中会记录同一 query 下的 local 文档、modular 文档、耗时和错误信息。

## 7. 失败降级

Modular 不可用、超时、collection 不存在或返回错误时：

- 用户正式回答不受影响。
- 本地 `KnowledgeService.search()` 仍是正式结果来源。
- `logs/rag_eval/shadow_eval.jsonl` 中记录 `modular.ok=false` 和 `modular.error`。
- 不会抛出异常中断首页咨询流程。

## 8. Primary 模式现状

Primary 模式已作为默认主检索配置支持，并已完成主检索层真实联调。它仍保留本地 FAISS fallback：

- Modular RAG 成为主检索源。
- 本地 FAISS 保留 fallback。
- Modular 超时或失败时自动回退到 `KnowledgeService.search()`。

第 7E 联调确认：

- 当前项目通过 `mcp_stdio` 子进程调用 Modular 的 `query_knowledge_hub`。
- `tutoring_course_kb` 已导入 8 条家教课程知识。
- Modular 独立查询可命中试听课、课时包、老师匹配、线上课和线下课规则。
- 当前项目 primary 检索层日志可记录 `final_source=modular_primary`。
- Modular 不可用时日志记录 `final_source=local_fallback`，正式用户回答不暴露 MCP error。

该验证是 RAG 主检索层联调，不等同于完整外部 LLM 端到端回答链路联调。
- PromptBuilder 尽量不大改，只适配统一的 `knowledge_docs` 结构。

详细切换方式见 `docs/RAG_PRIMARY_SWITCH_GUIDE.md`。
