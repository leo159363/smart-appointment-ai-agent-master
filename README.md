# AI 家教培训机构智能咨询与排课系统

## 1. 项目简介

AI 家教培训机构智能咨询与排课系统是一个面向家教/教培机构的智能咨询与排课 MVP。项目基于 FastAPI、多 Agent 任务分发、RAG 课程知识库和 SQLite 演示数据，支持课程咨询、老师匹配、试听课预约、正式排课、学习需求分析和知识库管理。

这个项目的重点不是单点功能演示，而是完整展示一次“领域迁移 + 可运行 MVP + 测试基线 + 页面/API 验收”的工程过程。系统将课程咨询、老师匹配、排课流程、知识库问答和学习需求分析串成一个可启动、可演示、可复验的应用。

项目基于原预约系统进行领域迁移和工程化改造，重点验证多 Agent + RAG + 排课咨询场景的可运行 MVP。为降低迁移风险，MVP 阶段保留部分历史内部字段命名，例如 `technician`、`appointment`、`service_type`，但对外页面、API 文档和演示数据已迁移为老师、课程、试听课和排课语义。

## 2. 核心功能

### 智能咨询助手

- 识别用户是在咨询课程、询问收费、匹配老师、预约试听课，还是提出无关问题。
- 回答课程体系、收费规则、老师介绍、试听课规则、排课规则和教学质量相关问题。
- 在模型不可用或问题超出范围时提供清晰的家教场景 fallback 文案。

### 多 Agent 任务分发

- 任务分类 Agent：判断用户输入属于课程咨询、试听课预约、正式排课或无关问题。
- 课程咨询 Agent：结合课程知识库回答机构课程、收费、老师和规则问题。
- 预约/排课 Agent：围绕学生年级、学科、薄弱点、学习目标、上课时间和老师偏好推进预约流程。
- 学习需求分析 Agent：分析学生/家长偏好，并生成学习跟进提醒。

### RAG 课程知识库

- 课程体系：小学、初中、高中一对一课程和专项辅导。
- 收费规则：试听课、课时包、课程包和退费说明。
- 老师介绍：教学方向、适合年级、授课风格和匹配依据。
- 试听/排课规则：试听预约、正式排课、改约、请假和补课。
- 教学质量说明：课堂反馈、阶段测评、错题复盘和家长回访。

### 老师管理与状态查看

- 查看老师列表。
- 查看授课方向和适合学生类型。
- 展示教学风格和可授课状态。
- 页面路径保留兼容路由，但对外展示为老师状态和老师课表。

### 试听课预约与正式排课

- 提取学生年级、学科、薄弱点和学习目标。
- 收集可上课时间、上课方式和老师风格偏好。
- 支持试听课预约和正式排课语义。
- 对排课信息缺失、老师时间冲突等情况进行追问或提示。

### 学习需求分析

- 分析学生/家长偏好。
- 生成学习跟进提醒。
- 支持回访消息生成，用于课程顾问后续沟通。

### 演示数据重置

- 提供 `scripts/reset_demo_data.py`。
- 可备份并重置本地 SQLite 演示数据。
- 写入家教培训场景课程知识库和老师样例。
- 不修改数据库 schema。

### 测试与验收基线

- `import app` smoke test。
- `pytest --collect-only` 测试收集。
- `task_classification` 单测回归。
- 页面/API 手工验收。
- 旧场景关键词扫描。
- A/B/C/D/E 风险分类记录。

## 3. 技术栈

| 层面 | 技术 |
| --- | --- |
| Backend | FastAPI、Uvicorn |
| Agent | 多 Agent 任务分发、Prompt 构造、Fallback 处理 |
| RAG | LangChain、FAISS、Embedding、课程知识库 |
| Database | SQLite、SQLAlchemy |
| Frontend | Jinja2 Templates、HTML/CSS/JavaScript |
| Testing | pytest、pytest-asyncio |
| Script | `scripts/reset_demo_data.py` |

## 4. 系统架构

```text
Web 前端页面
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
```

各层职责：

- `web/templates/`：前端页面展示，包括首页、知识库、老师状态、老师课表和学习需求分析。
- `web/routes.py`：页面路由和模板渲染。
- `api/`：REST API 接口，封装课程咨询、任务分类、预约、老师、知识库和学习需求分析能力。
- `agents/`：任务分类、课程咨询、预约/排课和学习需求分析的 Agent 流程。
- `services/`：知识库、老师、预约、用户行为、推荐和 Embedding 等业务服务。
- `db/`：SQLite 数据模型、Session 管理和 Repository 数据访问。
- `scripts/`：本地演示数据重置脚本。
- `tests/`：自动化测试基线。

## 5. 快速启动

### 1. 创建虚拟环境

```powershell
python -m venv .venv
```

### 2. 安装依赖

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env`，并配置 OpenAI-compatible 的聊天模型和 Embedding 服务。不要把真实 API Key 提交到 Git。

```powershell
Copy-Item .env.example .env
```

需要配置的方向包括：

- 聊天模型 API Key、Base URL、Model Name。
- Embedding 模型 API Key、Base URL、Model Name。
- SQLite 数据库连接地址，默认使用本地 `data/smart_appointment.db`。

### 4. 重置演示数据

```powershell
.\.venv\Scripts\python.exe scripts/reset_demo_data.py
```

脚本会备份当前 SQLite 文件，清理本地演示数据，并写入家教培训机构场景的课程知识库和老师样例。

### 5. 启动服务

```powershell
.\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
```

如果 8000 端口被占用，可以换成其他端口，例如：

```powershell
.\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8001
```

### 6. 访问页面

启动后访问：

- 首页：http://127.0.0.1:8000/
- Swagger API 文档：http://127.0.0.1:8000/docs

## 6. 页面入口

| 页面 | 地址 | 说明 |
| --- | --- | --- |
| 首页 | http://127.0.0.1:8000/ | 智能咨询与排课入口 |
| Swagger API 文档 | http://127.0.0.1:8000/docs | FastAPI 自动文档 |
| 知识库管理 | http://127.0.0.1:8000/knowledge | 课程知识库管理和搜索 |
| 老师状态 | http://127.0.0.1:8000/technician | 老师列表、授课方向和状态 |
| 老师课表 | http://127.0.0.1:8000/technician_schedule | 老师可授课时间和课表展示 |
| 学习需求分析 | http://127.0.0.1:8000/user_behavior_analysis | 学生偏好和学习跟进提醒 |

说明：部分 URL 保留 `technician` 等兼容路由命名，但页面展示和 API 文档语义为老师、课程、试听课和排课。

## 7. API 能力

| API 路径 | 能力 |
| --- | --- |
| `/api/knowledge` | 课程知识库查询、搜索、增删改 |
| `/api/technicians` | 老师数据和老师课表查询 |
| `/api/appointment` | 试听课预约与正式排课 |
| `/api/consultation` | 课程咨询问答 |
| `/api/user-behavior` | 学习需求分析和学习跟进提醒 |
| `/api/task` | 课程咨询与排课任务分类 |

详细请求参数和响应结构可在启动后通过 `/docs` 查看。

## 8. 演示数据重置

`scripts/reset_demo_data.py` 用于本地演示前重建家教培训机构场景数据。

脚本会执行：

- 备份当前 SQLite 数据库。
- 清理旧演示数据。
- 写入课程知识库示例。
- 写入老师演示数据。
- 保持数据库 schema 不变。

当前 `data/smart_appointment.db` 不强制提交到 Git。推荐通过 seed 代码和 `scripts/reset_demo_data.py` 重建演示数据，避免提交本地数据库和备份文件。

## 9. 测试与验收

当前测试基线：

- `import app` 可通过。
- `pytest --collect-only` 可收集 30 个测试。
- `tests/test_task_classification_agent.py` 当前存在 1 个已知失败，主要受 LLM/OpenAI-compatible 连接失败影响。
- 页面、API、SQLite 演示数据旧场景关键词扫描已通过。
- 当前质量策略是：先建立基线、分阶段迁移、分类记录失败，不为全绿而盲目修改核心逻辑。

验证命令：

```powershell
.\.venv\Scripts\python.exe -c "import app; print('app import ok')"
```

```powershell
.\.venv\Scripts\python.exe -m pytest --collect-only
```

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_task_classification_agent.py -q
```

当前已知测试结果示例：

```text
pytest --collect-only: collected 30 items
test_task_classification_agent.py: 1 failed, 7 passed
```

## 10. 项目迁移与质量控制

这个项目的工程重点之一是迁移过程本身的质量控制。

迁移过程包括：

1. 建立领域迁移映射文档。
2. 制定迁移计划和风险分级。
3. 建立测试基线和失败分类。
4. 分阶段迁移 README、默认数据、Agent prompt、前端页面、API 文档和演示数据库。
5. 手工验收页面、API 和 SQLite 演示数据。
6. 扫描旧场景关键词，确认对外展示没有残留。
7. 将问题分为 A/B/C/D/E 类，避免把外部依赖失败、测试不一致和真实数据问题混在一起。
8. 使用 `reset_demo_data.py` 保证演示数据可重建。

风险分类：

| 分类 | 含义 |
| --- | --- |
| A 类 | LLM/OpenAI-compatible 等外部依赖失败 |
| B 类 | 测试与当前实现不一致 |
| C 类 | SQLite 或数据处理问题 |
| D 类 | 页面/API/演示数据旧场景文案残留 |
| E 类 | 真实功能阻塞问题 |

这个过程能体现测试开发中的基线意识、回归验证、风险隔离和提交前验收能力。

## 11. 已知问题

当前 MVP 的边界如下：

1. LLM/OpenAI-compatible 连接失败会影响部分 Agent 单测。后续建议引入 fake/mock LLM provider，提高自动化测试稳定性。
2. MVP 阶段保留 `technician`、`appointment`、`service_type` 等内部兼容字段，避免大范围重构数据库、Repository 和 API 路由。
3. SQLite 演示数据通过 `scripts/reset_demo_data.py` 重建，不建议直接提交本地数据库和备份文件。
4. 全量 pytest 中仍有历史基线失败，后续应按 A/B/C 风险分类逐步修复。

这些问题不影响当前家教培训机构 MVP 的页面展示、API 演示和领域迁移说明。

## 12. 后续优化方向

- 引入 fake/mock LLM provider，提高 Agent 测试稳定性。
- 补充 API 自动化测试。
- 增加 Playwright 页面自动化验收。
- 增加 RAG 检索效果评估。
- 重构内部兼容字段命名。
- 完善 CI 流水线。
- 增加 Docker 部署。
- 增加学生、家长、老师、课程顾问等多角色权限管理。
