# 系统架构

## 1. 分层视图

```text
用户 / 浏览器
  ↓
Web 前端 Jinja2 Templates
  ↓
FastAPI Web Routes
  ↓
API 接口层
  ↓
Agent 层
  ↓
Service 层
  ↓
SQLite / FAISS / Knowledge Base
  ↓
Tests / Scripts / CI
```

## 2. Web 前端层

`web/templates/` 保存 Jinja2 页面模板，负责首页咨询入口、课程知识库管理、老师状态、老师课表、学习需求分析和后台管理页面展示。

`web/routes.py` 负责页面路由，包括：

- `/`：首页和智能咨询入口。
- `/knowledge`：课程知识库管理页面。
- `/technician`：老师状态页面；内部路径仍沿用旧版 `technician` 命名。
- `/technician_schedule`：老师课表页面。
- `/user_behavior_analysis`：学习需求分析页面。
- `/admin` 和 `/admin/database`：系统管理与数据库概览页面。

## 3. FastAPI 与 API 层

`app.py` 创建 FastAPI 应用，注册 Web 路由和 API 路由，并在启动阶段初始化知识库和老师演示数据。

`api/` 负责 REST API，包括：

- `api/chat_handler.py`：聊天入口，连接前端对话与 Agent 编排。
- `api/task.py`：课程咨询与排课任务分类接口。
- `api/consultation.py`：课程咨询问答接口。
- `api/appointment.py`：试听课预约或正式排课接口。
- `api/knowledge.py`：课程知识库查询、搜索和管理接口。
- `api/technician.py`：老师信息、状态和课表接口；路径和部分字段保留 `technician` 兼容命名。
- `api/user_behavior_analysis.py`：学习需求分析和跟进提醒接口。

## 4. Agent 层

`agents/` 负责智能任务处理和业务推理：

- `agents/task_classification_agent.py` 和 `agents/task_classification/agent_router.py`：识别用户意图，将请求路由到咨询、预约排课或其他处理分支。
- `agents/consultant_agent.py` 与 `agents/consultant/`：处理课程咨询，调用知识检索并生成面向家长的回答。
- `agents/appointment_agent.py`：处理试听课预约、正式排课信息收集和状态管理。
- `agents/user_behavior_agent.py`：分析用户行为、学习需求、偏好老师和跟进建议。

当前 Agent 层仍依赖真实 LLM/OpenAI-compatible Provider 初始化，因此 CI 只做模块导入和测试收集，不把真实 LLM 调用作为阻塞项。

## 5. Service 层

`services/` 封装核心业务能力：

- `services/knowledge_service.py`：课程知识加载、Embedding 生成、FAISS 索引构建和 `KnowledgeService.search()` 检索入口。
- `services/technician_service.py`：老师演示数据、老师状态和课表查询；内部命名保留 `technician` 兼容。
- `services/appointment_service.py`：预约和排课数据处理。
- `services/user_behavior_service.py`：用户行为记录和学习需求分析数据处理。

Embedding 和模型 Provider 配置由 `config/model_provider.py` 管理。数据库连接配置默认指向 `sqlite:///data/smart_appointment.db`。

## 6. 数据与知识库

SQLite 用于保存本地演示数据，包括课程知识、老师、预约、用户行为等信息。默认数据库路径为：

```text
data/smart_appointment.db
```

课程知识保存在 `knowledge_documents` 表中。`KnowledgeService` 初始化时加载活跃知识，生成 embedding，并构建 FAISS 本地向量索引，作为本地 fallback。默认 primary 模式下咨询 Agent 优先通过 `KnowledgeRetriever` → `RagMcpClient` 走 Modular RAG MCP Server 主检索，失败时自动回退本地 FAISS。

当前默认正式业务咨询链路优先使用 MODULAR-RAG-MCP-SERVER，FAISS 作为本地 fallback 保留。项目通过 `RAG_MCP_MODE` 支持三种模式：

- `local`：只使用本地 `KnowledgeService.search()`，用于不启动 Modular RAG 时的本地模式。
- `shadow`：正式回答仍使用本地 RAG，后台旁路调用 MODULAR-RAG-MCP-SERVER 记录对比日志。
- `primary`：默认模式，正式回答优先使用 MODULAR-RAG-MCP-SERVER；服务不可用、超时、返回空文档或报错时自动回退本地 FAISS。

因此本地 RAG 没有被删除，Modular RAG 是默认 primary 主检索源，本地 FAISS 为 fallback。

## 7. Scripts

`scripts/reset_demo_data.py` 用于重置本地演示数据，适合面试或演示前恢复默认老师、课程知识、预约和行为数据。

`scripts/export_tutoring_kb_for_modular_rag.py` 用于把当前 SQLite 中的活跃课程知识导出为 JSON，服务于后续 MODULAR-RAG-MCP-SERVER Eval-only 评估准备。该脚本只读数据库，不替换当前业务 RAG。

## 8. Tests 与 CI

`tests/` 保存当前测试基线，覆盖预约 Agent、咨询 Agent、任务分类 Agent 和用户行为 Agent 等模块。当前 CI 执行 `pytest --collect-only`，用于确认测试可发现、包路径可导入，不执行真实 LLM 调用。

GitHub Actions 工作流位于 `.github/workflows/ci.yml`，当前执行：

- checkout 代码。
- setup Python 3.11。
- 安装项目依赖和 `pytest`。
- 创建 `data/`、`exports/` 运行目录。
- `import app` smoke test。
- `pytest --collect-only`。
- RAG 导出脚本 `py_compile`。
- RAG/MCP 配置、client 和 logger `py_compile`。
- RAG 导出脚本 `--help`。

## 9. 学生画像记忆链路

学生画像记忆是现有用户行为体系上的最小扩展，不新增数据表。`services/student_profile_service.py` 复用 `UserBehaviorService` 写入 `user_behaviors` 表，使用 `action_type="student_profile_update"` 标识画像更新事件，并把 `grade`、`subject`、`weak_points`、`learning_goal`、`available_time`、`teacher_style_preference` 保存到 `action_data` JSON。

写入链路有两类入口：`/api/consultation/ask` 在处理非流式课程咨询前从 `question` 中提取画像并以 `source="consultation_api"` 记录；首页 `/chat` 会把 `ChatRequest.user_id` 传入 `ProcessUserInput_stream`，咨询类消息由 `ConsultantAgent` 自动提取并以 `source="chat"` 记录。`/chat/stream` 保持原调用方式，未接入该 user_id 同步。

读取链路分为咨询和预约两类。咨询链路中，`ConsultantAgent` 通过 `StudentProfileService.get_profile(user_id)` 获取最新画像，并用 `format_profile_context()` 生成短文本，交给 `PromptBuilder` 作为“补充学生画像上下文”，不会覆盖知识库和 RAG 检索结果。预约链路中，`AppointmentAgent` 读取画像后只把学科、可上课时间、老师风格偏好交给 `MessageBuilder.create_student_profile_suggestions()` 生成缺失字段提示，不写入 `appointment_history`，因此不会自动下单或替用户确认。

兼容边界：没有画像时 `get_profile()` 返回空字典，原咨询和预约流程保持不变；没有传 `user_id` 时使用 `default_user`；用户当前明确输入的课程、时间或偏好优先级高于历史画像。
