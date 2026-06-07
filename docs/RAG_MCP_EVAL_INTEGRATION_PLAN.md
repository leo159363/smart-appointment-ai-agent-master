# RAG/MCP Eval-only 接入计划

## 1. 当前状态

当前项目内置轻量 RAG，主要由 SQLite 课程知识表、Embedding 和 FAISS 索引组成。`KnowledgeService.search()` 是当前正式检索入口，咨询 Agent 通过 `agents/consultant/knowledge_retriever.py` 获取知识片段，再交给响应生成链路。

`MODULAR-RAG-MCP-SERVER-main` 尚未替换当前业务 RAG，也没有接入首页咨询、预约、老师匹配或学习需求分析流程。本阶段只完成 Eval-only 评估准备，不改变现有 MVP 的正式回答路径。

## 2. 为什么不直接替换现有 RAG

当前 MVP 已经围绕本地 `KnowledgeService.search()` 跑通，直接替换会影响咨询 Agent、PromptBuilder、接口返回结构和页面演示稳定性。

另外，Modular RAG 项目的数据导入格式还需要和当前 SQLite 知识表适配。当前评估指标和 golden test set 尚未建立，在缺少可量化基线前，不适合把 Modular RAG 直接变成主检索链路。

## 3. Eval-only 方案

Eval-only 阶段只做三件事：

1. 从 SQLite `knowledge_documents` 导出活跃课程知识 JSON。
2. 准备 `tutoring_course_kb` collection 的后续导入数据。
3. 使用 `tutoring_rag_golden_set.json` 作为课程咨询评估集。

后续可在 `MODULAR-RAG-MCP-SERVER-main` 中基于该数据集运行 `hit_rate`、`mrr`、`faithfulness`、`context_precision` 等指标。当前家教系统业务回答不受影响。

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

## 7. 后续 Shadow 模式

Shadow 阶段仍让当前业务使用本地 `KnowledgeService.search()` 返回正式答案，同时后台旁路调用 Modular RAG 查询相同问题。

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

## 8. 后续 Primary 模式

当 Eval-only 和 Shadow 指标稳定后，才考虑让 Modular RAG 成为主检索源。本地 FAISS 必须保留为 fallback。

Primary 模式的边界：

- MCP 超时或失败时自动降级到本地 `KnowledgeService.search()`。
- 尽量不大改 `PromptBuilder`。
- 通过适配层把 Modular 返回结果转换成当前 `knowledge_docs` 结构。
- 保持首页咨询、预约、老师匹配和学习需求分析的现有 MVP 行为可回退。

## 9. 风险与边界

- 当前 DB 只有 8 条活跃知识，评估集不能超出知识覆盖边界。
- 两个项目的 embedding 配置可能不同，检索结果不一定完全可比。
- Ragas 类指标可能依赖 LLM 或 embedding 外部服务，可能出现外部连接失败。
- 当前阶段不保证完整 MCP 生产接入。
- 当前阶段不影响原 MVP，也不替换 `KnowledgeService.search()`。
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
