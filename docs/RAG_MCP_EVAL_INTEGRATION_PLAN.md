# RAG/MCP Eval-only 接入计划

## 1. 当前状态

当前项目内置轻量 RAG，主要由 SQLite 课程知识表、Embedding 和 FAISS 索引组成。`KnowledgeService.search()` 是当前正式检索入口，咨询 Agent 通过 `agents/consultant/knowledge_retriever.py` 获取知识片段，再交给响应生成链路。

当前已完成 Eval-only、Shadow 和 Primary 三个阶段的接入准备与代码实现。第 7E 已完成 Primary 主检索层真实联调：当前项目可通过 `mcp_stdio` 调用 Modular 的 `query_knowledge_hub` 检索 `tutoring_course_kb`，并在 Modular 不可用、超时或返回空文档时自动 fallback 到本地 FAISS。默认模式仍是 `local`，未宣称完整首页 LLM 端到端回答链路已完成真实外部 LLM 联调。

## 2. 为什么不直接替换现有 RAG

当前 MVP 已经围绕本地 `KnowledgeService.search()` 跑通，直接替换会影响咨询 Agent、PromptBuilder、接口返回结构和页面演示稳定性。

另外，Modular RAG 项目的数据导入格式还需要和当前 SQLite 知识表适配。当前评估指标和 golden test set 尚未建立，在缺少可量化基线前，不适合把 Modular RAG 直接变成主检索链路。

## 3. Eval-only 方案

Eval-only 阶段只做三件事：

1. 从 SQLite `knowledge_documents` 导出活跃课程知识 JSON。
2. 准备 `tutoring_course_kb` collection 的后续导入数据。
3. 使用 `tutoring_rag_golden_set.json` 作为课程咨询评估集。

该导出数据已用于 `tutoring_course_kb` 的本地联调导入。后续仍可在 `MODULAR-RAG-MCP-SERVER-main` 中基于该数据集运行 `hit_rate`、`mrr`、`faithfulness`、`context_precision` 等指标。默认 local 模式下，当前家教系统业务回答不受影响。

## 4. 当前新增文件

- `scripts/export_tutoring_kb_for_modular_rag.py`
- `tests/fixtures/tutoring_rag_golden_set.json`
- `docs/RAG_MCP_EVAL_INTEGRATION_PLAN.md`

这些文件只用于 Eval-only 准备，不替换现有 RAG 链路。

## 5. 数据导出格式

导出 JSON 是数组，每个元素对应一条活跃课程知识：

- `id`: 导出 ID，例如 `kb_001`。
- `source_id`: 原始 `knowledge_documents.id`。
- `category`: 原始知识分类。
- `title`: 当前数据库没有 title 字段，暂时由 `category` 派生。
- `content`: 原始知识内容。
- `tags`: 由 `keywords` 转换而来；为空时是空数组。
- `source`: 固定为 `smart_appointment_db`。
- `domain`: 固定为 `tutoring`。
- `is_active`: 原始活跃状态布尔值。
- `created_at`: 数据库原值，不伪造。
- `updated_at`: 数据库原值，不伪造。

导出时不包含 `embedding` 字段。Modular RAG 后续应使用自己的 embedding pipeline 重新建立索引。

## 6. Golden Test Set 设计

`tests/fixtures/tutoring_rag_golden_set.json` 覆盖以下课程咨询场景：

- 试听课规则。
- 10 课时包和 20 课时包区别。
- 初二数学基础补弱老师匹配。
- 高一物理考前冲刺。
- 线上课和线下课区别。
- 正式排课需要确认的信息。
- 退费、改课、请假和补课规则。
- 老师匹配依据。
- 学习需求分析。
- 教学质量跟踪。

每条 case 包含 `query`、`expected_categories`、`expected_keywords`、`ideal_answer`、`must_not_include` 和 `difficulty`。`must_not_include` 保留旧场景词，用于后续评估旧文案污染。

## 7. Shadow 模式状态

Shadow 阶段已完成接入。该模式仍让当前业务使用本地 `KnowledgeService.search()` 返回正式答案，同时后台旁路调用 Modular RAG 查询相同问题。

建议记录：

- `query`
- local top_k
- modular top_k
- 命中文档
- `hit_rate`
- `mrr`
- `context_precision`
- 耗时
- 最终是否采用本地答案

MCP 服务失败、超时或返回空结果时，只记录日志，不影响用户正式回答。

当前项目已新增可选 Shadow 旁路接入。默认 `RAG_MCP_MODE=local`，完全不调用 Modular RAG；只有设置 `RAG_MCP_MODE=shadow` 后，`agents/consultant/knowledge_retriever.py` 才会在本地 RAG 返回正式结果后，后台调用 `RagMcpClient` 并通过 `RagEvalLogger` 写入 `logs/rag_eval/shadow_eval.jsonl`。

该接入不是 Primary 替换，不改变 `KnowledgeService.search()`，也不改变 PromptBuilder、API 路由、数据库 schema 或页面流程。

Modular 项目当前确认的直接入口是 stdio MCP server 和 `scripts/query.py` CLI；本项目 Shadow client 同时预留 HTTP adapter 调用方式，便于后续如果给 Modular 包装 HTTP 服务时复用。

## 8. Primary 模式状态

Primary 模式已完成代码接入，并已完成主检索层真实联调。本地 FAISS 必须保留为 fallback。当前项目支持可选 `RAG_MCP_MODE=primary`，但默认仍是 `local`。

Primary 模式的边界：

- MCP 超时或失败时自动降级到本地 `KnowledgeService.search()`。
- 尽量不大改 `PromptBuilder`。
- 通过适配层把 Modular 返回结果转换成当前 `knowledge_docs` 结构。
- 保持首页咨询、预约、老师匹配和学习需求分析的现有 MVP 行为可回退。
- 不删除或废弃本地 `KnowledgeService.search()`。

第 7E 真实联调结果：

- `tutoring_course_kb` collection 已导入 8 条家教课程知识。
- Modular 独立查询可命中试听课、课时包、老师匹配、线上课和线下课规则。
- 当前项目 primary 检索层日志出现 `event=primary_used_modular`、`final_source=modular_primary`、`modular_ok=True`、`modular_count=3`。
- Modular Python 路径错误或服务不可用时，日志记录 `final_source=local_fallback`，用户链路不暴露 MCP error。

后续优化方向：

- 补充更多 `tutoring_course_kb` 知识。
- 增加 RAG 指标评估脚本。
- 统计 primary/shadow 日志中的 hit@k、MRR 和 latency。
- 引入 fake/mock LLM provider 后做完整端到端测试。
- 再考虑更深度替换或部署。

## 9. 风险与边界

- 当前 DB 只有 8 条活跃知识，评估集不能超出知识覆盖边界。
- 两个项目的 embedding 配置可能不同，检索结果不一定完全可比。
- Ragas 类指标可能依赖 LLM 或 embedding 外部服务，可能出现外部连接失败。
- 当前阶段不保证完整 MCP 生产部署。
- 默认 `local` 不影响原 MVP；`primary` 也保留本地 `KnowledgeService.search()` fallback。
- 当前阶段不修改 API 路由、数据库 schema、PromptBuilder 或页面。

## 10. 验证命令

```powershell
.\.venv\Scripts\python.exe scripts/export_tutoring_kb_for_modular_rag.py --dry-run
```

```powershell
.\.venv\Scripts\python.exe scripts/export_tutoring_kb_for_modular_rag.py --output exports/tutoring_course_kb.json --pretty
```

```powershell
.\.venv\Scripts\python.exe -c "import app; print('app import ok')"
```

```powershell
.\.venv\Scripts\python.exe -m pytest --collect-only
```
