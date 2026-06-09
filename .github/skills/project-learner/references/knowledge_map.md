# 项目知识点地图 - AI 家教培训机构智能咨询与排课系统

## D1 项目定位与领域迁移

| 知识点 | 内容 | 源码/文档 | 面试题 |
|---|---|---|---|
| D1.1 | 项目一句话定位 | `README.md`, `docs/DOMAIN_MIGRATION_MAP.md` | RQ01 |
| D1.2 | 为什么迁移到家教培训机构场景 | `docs/MIGRATION_PLAN.md` | RQ02 |
| D1.3 | 为什么保留 `technician` 等内部兼容字段 | `docs/DOMAIN_MIGRATION_MAP.md`, `agents/appointment/*`, `api/*` | RQ02, RQ06 |

## D2 FastAPI 与分层架构

| 知识点 | 内容 | 源码/文档 | 面试题 |
|---|---|---|---|
| D2.1 | FastAPI 启动、router 注册、startup 初始化 | `app.py` | RQ03, RQ14 |
| D2.2 | Web 页面路由与 `/chat/stream` | `web/routes.py`, `web/templates/index.html` | RQ03 |
| D2.3 | REST API 层边界 | `api/` | RQ03 |
| D2.4 | Service 层与 Repository 边界 | `services/`, `db/` | RQ03 |

## D3 多 Agent 任务分发

| 知识点 | 内容 | 源码/文档 | 面试题 |
|---|---|---|---|
| D3.1 | 任务分类 Agent | `agents/task_classification_agent.py`, `agents/task_classification/task_classifier.py` | RQ04, RQ05 |
| D3.2 | AgentRouter 与共享状态 | `agents/task_classification/agent_router.py`, `state_manager.py` | RQ04 |
| D3.3 | 为什么多 Agent 而不是单 Agent | `agents/` | RQ04 |
| D3.4 | LLM 连接失败为什么是 A 类问题 | `docs/BASELINE_REPORT.md`, `tests/test_task_classification_agent.py` | RQ05, RQ15 |

## D4 预约/排课流程

| 知识点 | 内容 | 源码/文档 | 面试题 |
|---|---|---|---|
| D4.1 | 自然语言排课信息抽取 | `agents/appointment/input_parser.py` | RQ06 |
| D4.2 | 缺失信息追问与中文字段映射 | `agents/appointment/message_builder.py`, `appointment_processor.py` | RQ06 |
| D4.3 | 老师匹配与可授课时间 | `agents/appointment/technician_finder.py`, `services/appointment_service.py` | RQ07 |
| D4.4 | 预约成功消息和课程准备提示 | `agents/appointment/appointment_processor.py` | RQ06 |
| D4.5 | 为什么 `duration/gender` 暴露影响用户体验 | `agents/appointment/message_builder.py` | RQ13 |

## D5 RAG 课程知识库

| 知识点 | 内容 | 源码/文档 | 面试题 |
|---|---|---|---|
| D5.1 | 默认课程知识库 seed 与本地 FAISS | `services/knowledge_service.py`, `scripts/reset_demo_data.py` | RQ08 |
| D5.2 | SQLite 文档存储与 embedding | `db/`, `services/knowledge_service.py` | RQ08 |
| D5.3 | FAISS 向量索引构建与检索 | `services/knowledge_service.py`, `services/text_embedding.py` | RQ08 |
| D5.4 | 课程收费/课时包兜底回答 | `agents/consultant/response_generator.py`, `prompt_builder.py` | RQ08 |
| D5.5 | RAG 检索质量评估 | `tests/`, future eval docs | RQ09 |
| D5.6 | Modular RAG MCP Primary 主检索 + local FAISS fallback | `config/rag_mcp_config.py`, `agents/consultant/knowledge_retriever.py`, `services/rag_mcp_client.py`, `docs/RAG_PRIMARY_SWITCH_GUIDE.md` | RQ10 |

## D6 老师数据服务与 Embedding 匹配

| 知识点 | 内容 | 源码/文档 | 面试题 |
|---|---|---|---|
| D6.1 | 默认老师数据 | `services/technician_service.py`, `scripts/reset_demo_data.py` | RQ07 |
| D6.2 | 老师教学方向相似度匹配 | `agents/appointment/technician_finder.py`, `services/text_embedding.py` | RQ07 |
| D6.3 | 为什么内部仍叫 technician | `docs/DOMAIN_MIGRATION_MAP.md` | RQ02 |

## D7 学习需求分析

| 知识点 | 内容 | 源码/文档 | 面试题 |
|---|---|---|---|
| D7.1 | 行为记录与偏好分析 | `agents/user_behavior_agent.py`, `agents/user_behavior/` | RQ13 |
| D7.2 | 回访提醒和建议试听/排课时间 | `agents/user_behavior_agent.py`, `api/user_behavior_analysis.py` | RQ13 |
| D7.3 | `[object Object]` 与 `default_user` 展示问题 | `web/templates/user_behavior_analysis.html` | RQ13 |

## D8 测试基线与质量保障

| 知识点 | 内容 | 源码/文档 | 面试题 |
|---|---|---|---|
| D8.1 | import app smoke test | `docs/BASELINE_REPORT.md` | RQ15 |
| D8.2 | pytest collect-only 30 个测试 | `pytest.ini`, `tests/` | RQ15 |
| D8.3 | A/B/C/D/E 风险分类 | `docs/BASELINE_REPORT.md` | RQ15 |
| D8.4 | 页面/API/SQLite 演示数据验收 | `docs/BASELINE_REPORT.md`, manual validation notes | RQ12 |
| D8.5 | 旧文案关键词扫描 | `web/`, `api/`, `.agents/skills/` | RQ12 |

## D9 演示数据与运行环境

| 知识点 | 内容 | 源码/文档 | 面试题 |
|---|---|---|---|
| D9.1 | `reset_demo_data.py` 备份和重置 SQLite 数据 | `scripts/reset_demo_data.py` | RQ11 |
| D9.2 | `.env` 安全边界 | `.env.example`, `.gitignore` | RQ11 |
| D9.3 | 快速启动命令 | README, setup skill | RQ14 |
| D9.4 | 后续 mock/fake LLM、API 自动化、Playwright、CI | README, docs | RQ16 |
