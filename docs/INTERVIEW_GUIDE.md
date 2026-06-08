# 面试讲解指南

## 1. 3 分钟项目介绍

这是一套 AI 家教培训机构智能咨询与排课系统。项目最初来自通用预约系统，但原场景和我的家教经历、教培机构课程咨询场景不匹配，所以我把它迁移成了面向家长咨询、课程推荐、老师匹配、试听课预约、正式排课和学习需求分析的 MVP。

迁移不是简单改名字。我把 README、默认演示数据、Agent prompt、API 文档、前端页面、SQLite 数据和测试基线都迁移到教培语义。比如原来的服务预约被改造成试听课和正式排课，原来的技师语义对外迁移成老师语义，课程知识库覆盖试听规则、课时包、收费规则、老师介绍和教学质量跟踪。

系统架构上，前端使用 Jinja2 页面，后端是 FastAPI。用户从首页输入问题后，请求会进入 Web route 或 API 层，再由任务分类 Agent 判断是课程咨询、预约排课还是学习需求相关。咨询 Agent 会调用本地 RAG 知识库，预约/排课 Agent 会抽取年级、学科、薄弱点、时间、老师偏好和联系方式，学习需求分析 Agent 会基于行为数据生成偏好和回访建议。

RAG 部分当前默认优先走 MODULAR-RAG-MCP-SERVER 的 Primary 主检索模式。课程知识也保留在 SQLite 中，启动时由 `KnowledgeService` 加载活跃知识，生成 embedding，并构建 FAISS 索引作为本地 fallback。用户咨询课程包、试听规则或老师推荐时，系统优先检索 Modular RAG，失败、超时或空结果时回退本地 FAISS。

质量保障方面，我没有一开始追求全量测试全绿，而是先建立迁移基线：`import app` 保证应用入口可导入，`pytest --collect-only` 保证测试可发现，页面/API/SQLite 数据手工验收保证演示链路可用，并通过旧文案关键词扫描定位迁移残留。我还把问题分成 A/B/C/D/E 五类，区分 LLM 外部依赖、测试历史问题、SQLite 数据问题、旧文案残留和真实功能阻塞。

目前 GitHub Actions CI 已经跑绿，CI 会安装依赖、准备运行目录、导入 FastAPI app、收集 pytest 测试，并检查 RAG 导出脚本。当前已知边界是：内部仍保留 `technician` 等兼容字段，LLM 相关测试有外部连接依赖，后续会用 fake/mock LLM provider、API 自动化、Playwright 页面验收和 RAG golden set 评估继续增强。

## 2. 1 分钟简洁版

这个项目是 AI 家教培训机构智能咨询与排课系统，基于 FastAPI、多 Agent 和轻量 RAG 构建。它从通用预约系统迁移而来，迁移后支持课程咨询、老师匹配、试听课预约、正式排课和学习需求分析。

技术上，任务分类 Agent 负责判断用户意图，咨询 Agent 调用 SQLite + Embedding + FAISS 的本地 RAG 知识库，预约/排课 Agent 负责抽取信息并追问缺失项，学习需求分析 Agent 负责偏好和回访建议。质量上，我建立了 `import app`、pytest 收集、页面/API/SQLite 验收、旧文案扫描和 GitHub Actions CI。当前 CI 已跑绿，后续重点是 mock LLM、API 自动化、Playwright 和 RAG 评估。

## 3. 技术架构讲解

- Web 前端：`web/templates/` 提供首页、知识库管理、老师状态、老师课表和学习需求分析页面。
- FastAPI 路由：`web/routes.py` 提供页面入口和聊天入口，`app.py` 注册路由并初始化基础服务。
- API 层：`api/` 提供课程咨询、任务分类、预约排课、知识库、老师管理和学习需求分析接口。
- Agent 层：`agents/` 负责任务分类、咨询问答、预约排课和学习需求分析。
- Service 层：`services/` 封装知识库、老师、预约和用户行为逻辑。
- SQLite / FAISS：SQLite 保存演示数据和知识文档，FAISS 支持本地课程知识语义检索。
- Tests / Scripts / CI：`tests/` 提供测试基线，`scripts/` 提供演示数据重置和 RAG 导出，GitHub Actions 做基础质量检查。

## 4. 多 Agent 怎么讲

任务分类 Agent 负责判断意图，把用户输入分成课程咨询、试听预约、正式排课、学习需求分析或无关问题。

咨询 Agent 负责课程、收费、课时包、老师推荐、试听规则和线上线下课等问答。它会先检索知识库，再结合检索结果生成回答。

预约/排课 Agent 负责抽取年级、学科、薄弱点、期望时间、老师偏好和联系方式。如果信息不足，它不会直接创建成功预约，而是继续追问缺失信息。

学习需求分析 Agent 负责学生偏好、常见学习需求、跟进提醒和回访消息，适合展示机构如何做咨询后的持续跟进。

## 5. RAG 怎么讲

知识库保存课程体系、老师介绍、收费规则、试听/排课规则、课时包和教学质量跟踪等内容。

系统启动时从 SQLite 加载活跃知识，使用 embedding 模型生成向量，并构建 FAISS 索引。用户咨询时，`KnowledgeService.search()` 会检索相关知识片段，咨询 Agent 再把这些片段放入 prompt 中生成回答。

RAG Eval-only 阶段会把当前课程知识导出为 JSON，并使用 golden test set 评估试听课规则、课时包区别、老师推荐、线上线下课和教学质量跟踪等问题。

MODULAR-RAG-MCP-SERVER 目前是独立评估层和知识层，也是当前默认 Primary 检索源。当设置 `RAG_MCP_MODE=local` 时只用本地 `KnowledgeService.search()`；当设置 `RAG_MCP_MODE=shadow` 时正式回答用本地 RAG、旁路对比 Modular；默认 `RAG_MCP_MODE=primary` 时优先使用 Modular，失败后自动回退本地 RAG。

RAG/MCP Primary 真实联调可以这样讲：

“我没有直接硬替换本地 RAG，而是做了 local/shadow/primary 三种模式。当前已经完成 primary 检索层真实联调：系统优先通过 `mcp_stdio` 调用 Modular RAG MCP Server 的 `query_knowledge_hub`，在 `tutoring_course_kb` 中检索课程知识；如果 Modular 服务不可用、超时或返回空文档，则自动 fallback 到本地 FAISS。这样既完成了 Modular RAG 主检索接入，又保证咨询链路稳定。”

边界也要说清楚：这次验证的是 RAG 主检索层，不夸大为完整 LLM 端到端联调。

## 6. 测试开发怎么讲

迁移前先建立基线，不直接大面积改代码。基础基线包括 `import app` 验证应用入口、`pytest --collect-only` 验证测试可发现、目标测试识别已知失败范围。

迁移过程中每阶段小步修改，并用页面/API 手工验收、SQLite 数据复验和旧文案关键词扫描确认迁移质量。旧场景词如技师、顾客、防晒霜这类外显残留归为 D 类问题。

对失败进行 A/B/C/D/E 分类：A 类是 LLM/OpenAI-compatible 外部连接，B 类是测试与当前实现不一致，C 类是 SQLite 数据问题，D 类是旧文案残留，E 类是真实功能阻塞。

最后接入 GitHub Actions CI，让 push 后自动执行依赖安装、运行目录准备、`import app`、pytest 收集和 RAG 脚本检查。CI 不运行真实 LLM 测试，避免外部服务不稳定影响基础质量门禁。

## 7. 你见过并修过哪些 Bug

### 7.1 旧预约文案残留

- 现象：页面、默认知识和回答中残留技师、顾客、防晒霜等旧预约场景词。
- 定位：通过关键词扫描、页面检查和 SQLite 演示数据复验定位来源。
- 原因：项目从通用预约系统迁移，部分文案和默认数据没有同步更新。
- 修复：将对外语义迁移为老师、学生/家长、试听课、课程包和排课。
- 回归验证：复查页面/API/SQLite 数据，并继续保留迁移文档中的历史说明。

### 7.2 前端 `[object Object]` 展示问题

- 现象：学习需求分析页面把对象数组直接渲染成 `[object Object]`。
- 定位：检查页面模板和前端 JS 渲染逻辑。
- 原因：前端没有把结构化对象格式化成用户可读文本。
- 修复：将对象字段按老师、时间、建议等业务语义格式化展示。
- 回归验证：刷新学习需求分析页面，确认展示为中文业务内容。

### 7.3 `duration/gender` 内部字段暴露

- 现象：用户可见回答中出现 `duration`、`gender` 等内部字段。
- 定位：检查预约/排课消息构建和字段映射。
- 原因：内部兼容字段未转换为中文业务表达。
- 修复：把内部字段映射为课时时长、老师偏好等用户可理解描述。
- 回归验证：用试听课和老师偏好问题手工验证页面回答。

### 7.4 `default_user` 直接展示

- 现象：学习需求分析页面展示内部默认 user_id。
- 定位：检查 API 返回和页面展示字段。
- 原因：演示数据默认用户标识直接暴露给前端。
- 修复：改为展示学生/家长偏好和学习需求相关内容。
- 回归验证：刷新学习需求分析页面，确认不再外显内部 ID。

### 7.5 CI Missing credentials

- 现象：GitHub Actions 执行 `import app` 时报 Azure/OpenAI credentials 缺失。
- 定位：`import app` 会加载 Agent，初始化 LLM SDK。
- 原因：CI 环境没有 `.env` 和真实 API key。
- 修复：在 CI job env 中配置 dummy LLM/embedding 环境变量，仅用于 SDK 初始化。
- 回归验证：CI 中 `Import FastAPI app` 通过，且没有执行真实 LLM 调用。

### 7.6 CI unable to open database file

- 现象：CI 中 `import app` 报 SQLite `unable to open database file`。
- 定位：数据库默认路径是 `data/smart_appointment.db`。
- 原因：GitHub Actions checkout 不会自动包含空的 `data/` 目录。
- 修复：在 CI 的 import 前创建 `data/` 和 `exports/` 运行目录。
- 回归验证：`Prepare runtime directories` 和 `Import FastAPI app` 均通过。

### 7.7 CI No module named pytest

- 现象：CI 执行 `python -m pytest --collect-only` 时报 `No module named pytest`。
- 定位：检查 `requirements.txt`，发现没有 pytest。
- 原因：本地虚拟环境安装过 pytest，但 CI 新环境只安装运行依赖。
- 修复：在 CI 中额外安装 `pytest` 作为测试收集工具。
- 回归验证：GitHub Actions `Collect pytest tests` 通过，最终 CI 跑绿。

## 8. 常见追问回答

### 8.1 为什么不全局把 `technician` 改成 `teacher`？

当前阶段目标是把项目迁移成可运行、可演示的教培 MVP，而不是一次性重构所有内部命名。`technician` 牵涉数据库字段、API 路径、前端调用和测试基线，贸然全局替换容易引入路由和数据兼容问题。因此我先保证对外语义迁移为老师，内部兼容字段保留，后续再做分阶段重构。

### 8.2 为什么 CI 里用 dummy LLM 环境变量？

因为 `import app` 会初始化 Agent 和 LLM SDK。CI 只做模块导入和测试收集，不应该依赖真实 API key，也不应该调用真实模型。dummy 环境变量只是让 SDK 初始化通过，不代表真实请求。

### 8.3 为什么不把 `task_classification` 测试作为阻塞 CI？

当前 `task_classification` 相关测试仍受 LLM/OpenAI-compatible 外部连接影响。如果把它作为阻塞项，CI 会因为外部服务不稳定而失败，不能反映代码基础质量。后续引入 fake/mock LLM provider 后，再把这类 Agent 单测纳入阻塞 CI。

### 8.4 为什么当前只做 CI 不做 CD？

当前项目是本地 MVP 演示系统，还没有完整 Docker 镜像、云环境、数据库迁移和密钥管理。直接做 CD 容易把演示数据、模型配置和生产部署混在一起。当前先做 CI，保证基础质量门禁，后续生产化后再做 CD。

### 8.5 为什么 MODULAR-RAG-MCP-SERVER 先做 Eval-only/Shadow，再切到默认 Primary？

本地 `KnowledgeService.search()` 已经支撑咨询 MVP，直接硬替换会影响咨询回答、PromptBuilder、页面演示和 API 行为。所以我先做 Eval-only：导出知识、设计 golden set；再做 Shadow：旁路对比检索结果；最后切到 Primary 默认主检索，并保留本地 FAISS fallback。这样能验证检索质量，同时保证 Modular 服务不可用时用户回答不受影响。

### 8.6 这个系统是给学生家长用，还是给机构管理端用？

两者都有。首页咨询和预约链路面向学生家长，知识库、老师状态、课表和学习需求分析页面更偏机构管理端和面试演示端。当前 MVP 重点是展示完整业务链路，不是严格的生产权限系统。

### 8.7 知识库是什么，为什么需要知识库？

知识库保存课程体系、试听规则、课时包、收费规则、老师介绍和教学质量跟踪等稳定信息。咨询 Agent 不能只依赖模型记忆，否则回答容易不一致。RAG 让系统先检索本项目自己的课程知识，再生成回答，提高一致性和可控性。

### 8.8 如果后续继续优化，你会先做什么？

我会先引入 fake/mock LLM provider，让 Agent 单测稳定进入 CI；然后补 API 自动化和 Playwright 页面验收；再把 RAG golden set 自动评估接入 CI；最后持续验证 Modular RAG 的 Shadow/Primary 日志质量，并逐步重构内部兼容字段。
