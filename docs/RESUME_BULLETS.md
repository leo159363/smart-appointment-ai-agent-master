# 简历项目描述素材

## 1. 推荐项目名称

候选名称：

1. 基于多 Agent 与 RAG 的智能课程咨询系统
2. AI 家教培训机构智能咨询与排课系统
3. AI 驱动的教育咨询与排课自动化平台

最推荐用于测试开发实习简历的是：**基于多 Agent 与 RAG 的智能课程咨询系统**。

原因：这个名称既能体现 AI 应用能力，也能引出测试开发重点，包括 Agent 任务分发、RAG 知识检索、迁移测试基线、页面/API 验收和 CI 基础检查。相比直接写“家教培训机构”，它更适合简历筛选阶段抓住技术关键词。

## 2. 一句话项目描述

版本 1：

基于 FastAPI、多 Agent 任务分发与 RAG 知识库，构建面向家教培训机构的智能课程咨询、老师匹配、试听课预约、正式排课和学习需求分析系统。

版本 2：

将通用预约系统迁移为家教培训机构智能咨询与排课 MVP，覆盖 Agent prompt、课程知识库、SQLite 演示数据、页面/API 验收、测试基线和 GitHub Actions CI。

版本 3：

围绕教培机构课程咨询场景，设计多 Agent 协作链路和轻量 RAG 知识库，并通过测试基线、缺陷分类和 CI 检查保障迁移质量。

## 3. 三行简历版本

- 基于 FastAPI、Jinja2、多 Agent 编排和 SQLite + Embedding + FAISS 轻量 RAG，构建家教培训机构智能课程咨询与排课 MVP。
- 实现课程咨询、老师匹配、试听课预约、正式排课和学习需求分析等链路，并完成从通用预约系统到教培场景的领域迁移。
- 建立 `import app`、`pytest --collect-only`、页面/API/SQLite 验收和 GitHub Actions CI 基础检查，并补充 RAG Eval-only 导出脚本与 golden test set。

## 4. 测试开发版本 bullets

- 建立迁移测试基线，使用 `import app`、`pytest --collect-only` 和核心 Agent 单测识别迁移前后风险。
- 通过首页、API 文档、知识库、老师状态、课表和学习需求页面验收，验证 MVP 主链路可演示。
- 结合 API 返回、SQLite 演示数据和旧文案关键词扫描，定位通用预约场景残留。
- 设计 A/B/C/D/E 风险分类，区分 LLM 外部依赖、测试历史问题、SQLite 数据问题、文案残留和真实功能阻塞。
- 接入 GitHub Actions CI，在 push 后自动执行依赖安装、应用导入、测试收集和 RAG 脚本检查。
- 排查并修复 CI 环境问题，包括 dummy LLM 环境变量、SQLite 运行目录和 `pytest` 依赖缺失。
- 修复前端展示问题，如 `[object Object]`、`default_user`、`duration/gender` 等内部字段外显。
- 使用 `scripts/reset_demo_data.py` 重置课程知识、老师、预约和学习需求演示数据，保证演示稳定可复现。

## 5. Agent/RAG 版本 bullets

- 设计中心化多 Agent 任务分发，将课程咨询、预约/排课和学习需求分析拆分到不同处理链路。
- 使用任务分类 Agent 判断用户意图，并路由到咨询 Agent、预约/排课 Agent 或其他业务分支。
- 构建课程咨询 Agent，围绕课程体系、试听规则、课时包、收费规则和老师推荐生成回答。
- 实现预约/排课 Agent，抽取年级、学科、薄弱点、时间、老师偏好和联系方式，并追问缺失信息。
- 构建学习需求分析 Agent，输出偏好老师、学习需求、跟进提醒和回访消息。
- 使用 SQLite + Embedding + FAISS 实现本地轻量 RAG，`KnowledgeService.search()` 作为当前正式课程知识检索入口。
- 新增 RAG Eval-only 导出脚本，将活跃课程知识导出为后续评估层可适配 JSON。
- 设计 tutoring golden test set，并接入 MODULAR-RAG-MCP-SERVER 的 Shadow 对比和 Primary 主检索模式；默认 local，Primary 失败时回退本地 RAG。
- 接入 MODULAR-RAG-MCP-SERVER 作为可配置 RAG/MCP 检索层，支持 local、shadow、primary 三种模式；Primary 模式下优先调用 Modular 的 `query_knowledge_hub` 检索 `tutoring_course_kb`，失败时自动 fallback 到本地 FAISS，保证咨询链路可用性。
- 完成 Modular RAG 主检索层真实联调，导入 8 条家教课程知识并验证试听课、课时包、老师匹配、线上/线下课等查询命中结果，同时通过 jsonl 日志记录 `final_source`、`modular_count`、fallback 原因等评估信息。

## 6. 后端开发版本 bullets

- 基于 FastAPI 拆分 Web routes 与 REST API routes，支持首页聊天、课程知识库、老师状态、课表和学习需求分析页面。
- 在 Service 层封装知识库、老师、预约和用户行为逻辑，降低 Agent 层与 SQLite 数据访问耦合。
- 使用 SQLite 保存本地演示数据，并通过脚本化方式重建课程知识、老师数据和预约数据。
- 使用 Jinja2 模板构建可演示前端页面，配合 FastAPI `/docs` 展示 API 能力。
- 接入 GitHub Actions CI，完成依赖安装、应用导入、测试收集和 RAG 辅助脚本检查。
- 新增 RAG 知识导出脚本，为后续独立 RAG/MCP 评估层接入提供数据准备。

## 7. STAR 版本

**S：** 原系统是通用预约场景，和本人家教经历及教培机构课程咨询场景不匹配，直接用于简历和面试讲解缺少业务可信度。

**T：** 在保证系统可运行的前提下，将领域语义、默认数据、Agent prompt、API 文档、前端页面、SQLite 演示数据和测试基线迁移到家教培训机构场景。

**A：** 采用分阶段迁移方式，先建立 `import app`、pytest 收集和页面/API 验收基线，再逐步迁移默认数据、Agent 回答、页面文案和 API 说明；通过关键词扫描定位旧文案残留，按 A/B/C/D/E 分类记录风险；接入 GitHub Actions CI，并设计 RAG Eval-only 导出和 golden test set。

**R：** 完成可运行的家教培训机构智能咨询与排课 MVP，GitHub Actions CI 跑绿，`pytest --collect-only` 可收集 30 个测试，页面/API/SQLite 演示数据完成迁移验收；当前保留 LLM 外部依赖和内部兼容字段等 MVP 边界，后续计划通过 mock LLM、API 自动化、Playwright 和 RAG 评估继续增强。
