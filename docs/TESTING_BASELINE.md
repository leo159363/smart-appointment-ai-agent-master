# 测试基线与质量保障

## 1. 测试目标

项目迁移过程中，测试目标不是一开始追求全量 pytest 全绿，而是先保证基础可运行和可验收：

- 应用可导入。
- 测试可收集。
- 核心链路可手工验证。
- 旧场景文案不进入对外展示。
- CI 能自动执行基础检查。

这种策略适合迁移型 MVP：先建立边界清晰的质量基线，再逐步修复历史问题和外部依赖问题。

## 2. 当前基线命令

```powershell
.\.venv\Scripts\python.exe -c "import app; print('app import ok')"
```

```powershell
.\.venv\Scripts\python.exe -m pytest --collect-only
```

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_task_classification_agent.py -q
```

```powershell
.\.venv\Scripts\python.exe -m py_compile scripts/export_tutoring_kb_for_modular_rag.py
```

```powershell
.\.venv\Scripts\python.exe scripts/export_tutoring_kb_for_modular_rag.py --help
```

## 3. 当前测试状态

- `import app` 本地通过，可验证 FastAPI 应用入口可导入。
- `pytest --collect-only` 本地可收集 30 个测试。
- `task_classification` 仍有 1 个已知失败，主要受 LLM/OpenAI-compatible 外部连接影响。
- GitHub Actions CI 已通过基础检查。
- CI 不运行真实 LLM 测试，也不依赖真实 API key。

## 4. 手工验收范围

当前手工验收覆盖：

- 首页咨询与预约。
- `/docs` API 文档。
- `/knowledge` 知识库页面。
- `/technician` 老师状态页面。
- `/technician_schedule` 老师课表页面。
- `/user_behavior_analysis` 学习需求分析页面。
- API 返回结构和中文业务说明。
- SQLite 演示数据，包括课程知识、老师、预约和用户行为数据。
- 旧文案关键词扫描，包括技师、顾客、防晒霜等旧预约场景词。

## 5. A/B/C/D/E 风险分类

- A 类：LLM/OpenAI-compatible 连接失败。属于外部依赖问题，适合通过 fake/mock LLM provider 稳定测试。
- B 类：测试与当前实现不一致。通常来自迁移后接口语义、返回结构或历史测试预期未同步。
- C 类：SQLite 数据写入或初始化问题。包括本地数据库、演示数据重置、字段序列化和运行目录问题。
- D 类：页面/API/演示数据旧文案残留。包括旧业务词、内部字段外显和不符合教培场景的展示内容。
- E 类：真实功能阻塞问题。会影响首页咨询、预约排课、知识检索或页面核心展示，需要优先修复。

## 6. CI 检查内容

GitHub Actions 当前执行：

- checkout 代码。
- setup Python 3.11。
- install dependencies，并额外安装 `pytest`。
- prepare runtime directories，创建 `data/` 和 `exports/`。
- `import app` smoke test。
- `pytest --collect-only`。
- RAG export script `py_compile`。
- RAG/MCP 配置、client 和 logger `py_compile`。
- RAG export script `--help`。

CI 当前只做基础质量门禁，不做 CD 部署，不自动 commit，不运行真实 LLM 调用，也不启动真实 MODULAR-RAG-MCP-SERVER。

## 7. Modular RAG Primary 本地集成验证

Modular RAG Primary 真实联调属于本地集成验证，不是当前 GitHub Actions 的阻塞检查。CI 只做 `py_compile` 和基础导入、测试收集，避免依赖本机 Modular 服务、collection 数据或外部模型配置。

本地集成验证重点：

- Modular 独立查询成功，能够命中 `tutoring_course_kb`。
- 当前项目设置 `RAG_MCP_MODE=primary` 后，日志出现 `final_source=modular_primary`。
- Modular 不可用、Python 路径错误或返回空文档时，日志出现 `final_source=local_fallback`。
- 页面用户链路不暴露 MCP error，本地 `KnowledgeService.search()` fallback 保持可用。

该验证只说明 RAG 主检索层真实联调完成，不等同于完整外部 LLM 端到端回答链路已完成。

## 8. 后续测试计划

- 引入 fake/mock LLM provider，让任务分类和 Agent 单测脱离真实外部服务。
- 补充 API 自动化测试，覆盖课程咨询、预约排课、老师查询、知识库和学习需求分析接口。
- 使用 Playwright 做页面自动化验收，覆盖首页、知识库、老师状态、课表和学习需求页面。
- 将 RAG golden set 自动评估和 Shadow/Primary 日志分析接入 CI 或离线评估，覆盖 hit rate、MRR、context precision 和业务关键点检查。
- 在 CI 中加入更多稳定测试，逐步从 collect-only 过渡到阻塞性单测。
- CD 前增加 Docker build 检查，验证生产化镜像构建能力。
