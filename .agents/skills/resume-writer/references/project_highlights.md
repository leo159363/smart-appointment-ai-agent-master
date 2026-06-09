# 项目技术亮点清单

## 亮点 1：分阶段领域迁移与质量基线

**源码/文档锚点**：
- `docs/DOMAIN_MIGRATION_MAP.md`
- `docs/MIGRATION_PLAN.md`
- `docs/BASELINE_REPORT.md`
- `pytest.ini`

**可写法**：
- "建立迁移前测试基线，使用 `import app`、pytest collect-only、目标单测和页面/API 手工验收控制领域迁移风险。"
- "将旧业务语义按映射表迁移为老师、课程、试听课和排课语义，并通过关键词扫描定位外显残留。"

## 亮点 2：中心化 Multi-Agent 编排

**源码锚点**：
- `agents/task_classification_agent.py`
- `agents/task_classification/task_classifier.py`
- `agents/task_classification/agent_router.py`
- `agents/appointment_agent.py`
- `agents/consultant_agent.py`
- `agents/user_behavior_agent.py`

**可写法**：
- "设计中心化任务分发流程，将课程咨询、试听课预约、正式排课和学习需求分析拆分到不同 Agent，降低单 Agent 状态混乱风险。"

## 亮点 3：预约/排课状态管理与老师匹配

**源码锚点**：
- `agents/appointment/input_parser.py`
- `agents/appointment/appointment_processor.py`
- `agents/appointment/message_builder.py`
- `agents/appointment/technician_finder.py`
- `services/appointment_service.py`

**可写法**：
- "实现自然语言排课信息抽取与缺失信息追问，将内部字段映射为中文业务字段，避免向用户暴露兼容命名。"
- "基于老师教学方向、性别偏好和可授课时间完成老师匹配，并支持指定老师不可授课时的替代推荐。"

## 亮点 4：RAG 课程知识库

**源码锚点**：
- `services/knowledge_service.py`
- `agents/consultant/knowledge_retriever.py`
- `agents/consultant/prompt_builder.py`
- `agents/consultant/response_generator.py`

**可写法**：
- "构建 RAG 课程知识库，默认通过 Modular RAG MCP Server (primary 模式) 检索课程知识，本地 SQLite + FAISS 向量索引作为 fallback，覆盖课程规则、收费说明、老师介绍和试听/排课规则。"
- "针对收费和课时包咨询补充规则型兜底，提升演示阶段问答完整性。"

## 亮点 5：学习需求分析与回访提醒

**源码锚点**：
- `agents/user_behavior_agent.py`
- `agents/user_behavior/pattern_analyzer.py`
- `api/user_behavior_analysis.py`
- `web/templates/user_behavior_analysis.html`

**可写法**：
- "基于历史预约/咨询行为分析偏好老师、常选课程和常用时长，生成学习跟进消息和建议试听/排课时间。"
- "定位并修复页面对象数组直接渲染、内部 user_id 外显等演示体验问题。"

## 亮点 6：演示数据可重建

**源码锚点**：
- `scripts/reset_demo_data.py`
- `services/knowledge_service.py`
- `services/technician_service.py`

**可写法**：
- "新增演示数据重置脚本，备份并重建 SQLite 家教场景知识库和老师数据，保证面试演示可复现且不修改数据库结构。"

## 亮点 7：FastAPI 流式响应与页面验收

**源码锚点**：
- `web/routes.py`
- `web/templates/index.html`
- `api/chat_handler.py`

**可写法**：
- "基于 FastAPI StreamingResponse 和 AsyncGenerator 实现首页流式聊天，展示任务分类、Agent 路由和排课处理过程。"

## 亮点 8：测试开发包装价值

**源码/测试锚点**：
- `tests/`
- `docs/BASELINE_REPORT.md`

**可写法**：
- "将剩余失败按 A/B/C/D/E 分类记录，区分外部 LLM 连接、测试实现差异、SQLite 数据问题、页面文案残留和真实阻塞问题。"
- "后续计划引入 fake/mock LLM、API 自动化、Playwright 页面验收和 RAG 检索评估，提升回归稳定性。"

## 亮点 9：Modular RAG/MCP 主检索 + 本地 FAISS fallback

**源码锚点**：
- `config/rag_mcp_config.py`（默认 `primary` 模式）
- `agents/consultant/knowledge_retriever.py`（primary + fallback 逻辑）
- `services/rag_mcp_client.py`（MCP stdio/HTTP/CLI 三种 transport）
- `services/rag_eval_logger.py`（primary/shadow 对比日志）
- `MODULAR-RAG-MCP-SERVER-main/`

**可写法**：
- "已接入 Modular RAG MCP Server 作为默认 primary 主检索源，通过 `mcp_stdio` 调用 `query_knowledge_hub` 检索 `tutoring_course_kb`，本地 SQLite + FAISS 保留为 fallback。"
- "支持 local / shadow / primary 三种模式，通过 jsonl 日志记录 `final_source`、fallback 原因和 Modular 可用性，用于检索效果对比和质量评估。"

**边界**：
- Modular RAG 已是 primary 默认主检索源（不要写成未来方向），本地 FAISS 仍作为 fallback（不要写成已完全替换本地 RAG）。
