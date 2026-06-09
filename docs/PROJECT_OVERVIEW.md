# 项目概览

## 1. 项目定位

本项目是一个 AI 家教培训机构智能咨询与排课系统，面向教培机构的家长咨询、课程推荐、试听课预约、正式排课和学习需求分析场景。

系统基于 FastAPI 构建后端服务，通过多 Agent 协作完成任务识别、课程咨询、老师匹配、预约排课和用户行为分析。RAG 课程知识库采用双层架构：默认优先通过 Modular RAG MCP Server（primary 模式）检索课程知识，本地 SQLite + Embedding + FAISS 向量索引作为 fallback。

## 2. 核心能力

- 智能咨询：识别家长关于试听课、课程包、老师推荐、线上线下课、改课退费等常见问题。
- 多 Agent 协作：通过任务分类 Agent 将请求分发到咨询、预约排课和学习需求分析等能力模块。
- RAG 课程知识库：默认通过 Modular RAG MCP Server 主检索课程知识，本地 SQLite + Embedding + FAISS 作为 fallback，支持 local/shadow/primary 三种模式。
- 老师匹配：围绕学科、年级、基础情况、学习目标和时间偏好推荐合适老师。
- 试听课预约：支持从自然语言中提取学生、年级、科目、时间、联系方式等预约信息。
- 正式排课：在试听和沟通后支持正式课程安排的业务流程表达。
- 学习需求分析：根据用户行为和偏好信息生成学习需求、老师偏好和跟进建议。
- RAG/MCP 扩展：提供课程知识导出脚本、golden test set，并支持 MODULAR-RAG-MCP-SERVER 的 local、shadow、primary 三种模式；默认 primary，优先调用 Modular RAG，失败时回退本地 FAISS。
- CI 基础检查：GitHub Actions 已接入基础质量检查，包括依赖安装、`import app`、测试收集和 RAG 导出脚本检查。

## 3. 改造背景

项目最初来自通用预约系统，后续迁移到家教培训机构场景。迁移目标不是简单替换页面文案或改几个变量名，而是把业务语义、演示数据、Agent prompt、页面入口、API 说明和测试基线统一迁移到教培咨询与排课领域。

已完成的迁移覆盖范围包括：

- README 和项目说明中的业务定位。
- SQLite 演示数据和默认知识库内容。
- Agent prompt、任务分类语义和咨询回答边界。
- API 文档中的课程咨询、试听课预约、老师管理和学习需求分析描述。
- 前端页面中的家教培训机构展示、知识库管理、老师状态和课表页面。
- 测试基线和已知问题归类。
- GitHub Actions CI 基础检查。
- RAG Eval-only 导出脚本、评估集和接入计划文档。

## 4. 当前 MVP 边界

当前版本定位为本地 MVP 演示系统，不是完整生产系统。为了降低迁移风险和保持接口兼容，部分内部字段、路径和数据访问层仍保留 `technician` 等旧命名，但页面、API 说明和业务语义已经转向老师、课程咨询和排课场景。

当前边界包括：

- 业务主流程默认使用 Modular RAG MCP（primary 模式）作为主检索源，本地 `KnowledgeService.search()` 和 FAISS 作为 fallback。
- MODULAR-RAG-MCP-SERVER 已支持 Shadow 对比和 Primary 主检索模式；当前默认是 primary，但 Primary 不是硬替换，本地 FAISS 保留为 fallback。需要完全使用本地 RAG 时，可显式设置 `RAG_MCP_MODE=local`。
- CI 只执行基础质量检查，不执行真实 LLM 调用。
- LLM/OpenAI-compatible 相关测试仍存在外部服务依赖，后续应通过 mock/fake LLM provider 纳入稳定阻塞 CI。
- SQLite 数据库主要服务于本地演示，`data/smart_appointment.db` 可通过 `scripts/reset_demo_data.py` 重建，不作为生产数据库方案。

## 5. 项目价值

这个项目适合用于展示测试开发、Agent 应用、RAG 应用和工程化交付能力：

- 测试开发：有明确的测试基线、已知问题分类、CI 收集检查和后续自动化测试扩展方向。
- Agent 应用：包含任务分类、咨询、预约排课和用户行为分析等多 Agent 协作场景。
- RAG 应用：实现 Modular RAG MCP（主检索层）+ 本地 SQLite/Embedding/FAISS（fallback 层）的双层架构，支持 Eval-only、Shadow、Primary 模式切换和检索结果评估日志。
- 工程化交付：包含 FastAPI 服务、Jinja2 页面、SQLite 演示数据、脚本化数据重置、GitHub Actions CI 和分阶段文档。

## 6. 学生画像记忆系统

系统已增加最小学生画像记忆能力，用于在多轮咨询和预约排课中保留学生的基本学习背景。画像字段包括 `grade`、`subject`、`weak_points`、`learning_goal`、`available_time`、`teacher_style_preference`。

画像数据复用现有 `user_behaviors` 表保存，不新增数据库表，不修改数据库 schema。每次画像更新写入一条 `action_type="student_profile_update"` 的行为事件，`action_data` 保存画像字段 JSON；读取时按时间合并同一 `user_id` 的更新事件，得到最新画像。

在 `/api/consultation/ask` 和首页 `/chat` 咨询链路中，系统会从用户问题中用规则提取画像字段，非空时写入画像事件，再读取最新画像并作为补充上下文传入咨询 prompt。该上下文只做个性化参考，不替代 RAG 检索结果。

在预约/排课链路中，`AppointmentAgent` 会读取画像中的学科、可上课时间和老师风格偏好，用于缺失信息追问，例如建议是否预约之前提到的学科试听课、是否优先安排之前偏好的时间、是否按之前偏好的老师风格匹配。画像不会自动创建预约，不会替用户确认预约，也不会覆盖用户当前明确输入。
