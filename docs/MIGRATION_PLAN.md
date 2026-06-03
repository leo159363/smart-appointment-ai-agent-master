# 迁移计划

## 1. 迁移目标

将当前项目从“按摩门店智能预约系统”迁移为“AI 家教培训机构智能咨询与排课系统”。

本阶段不改核心业务代码，不改数据库模型，不改 API 路由，不做大规模全局替换。目标是先把领域迁移设计和基线状态落盘，为后续按阶段迁移 README、知识库、默认数据、Agent prompt、页面文案和测试用例提供明确执行顺序。

## 2. 迁移原则

1. 只处理 `smart-appointment-ai-agent-master`，不整合 `MODULAR-RAG-MCP-SERVER-main`。
2. 保留 FastAPI、LangChain、FAISS、SQLite、多 Agent 架构。
3. 不粗暴全局替换，避免破坏数据库模型、API 路由和跨层调用。
4. 对外文案优先迁移为家教机构场景，内部高风险命名可暂时保留，例如 `technician`、`appointment`、`service_type`。
5. 默认数据、prompt 和测试用例要体现课程咨询、老师匹配、试听课预约、正式排课和学习需求分析。
6. 每一阶段都先记录基线，再做小范围修改，再运行测试和启动检查。

## 3. 修改优先级

### P0：优先修改

- `README.md`
  - 项目名称、项目背景、核心能力、启动说明、测试说明、演示场景。
- `services/knowledge_service.py`
  - 默认知识库从按摩服务迁移为课程体系、收费规则、老师介绍、试听课规则、退费规则、上课须知。
- `services/technician_service.py`
  - 默认技师数据迁移为老师数据；字段名可先保留，内容改为学科、年级、教龄、教学风格。
- `agents/consultant/prompt_builder.py`
  - 咨询 Agent prompt 从按摩门店前台迁移为课程咨询顾问。
- `agents/task_classification/task_classifier.py`
  - 分类 prompt 增加课程咨询、试听预约、正式排课、学习需求分析、价格咨询等类别语义。
- `agents/task_classification/unrelated_handler.py`
  - 无关问题回复迁移为家教机构边界说明。
- `agents/appointment/input_parser.py`
  - 预约抽取语义从服务项目/技师偏好迁移为学科、年级、薄弱点、目标、老师风格、可上课时间。
- `agents/appointment/message_builder.py`
  - 缺失信息追问、预约成功、推荐老师、冲突提示等回复文案迁移为试听课/排课场景。
- `tests/*.py`
  - 测试输入、期望分类、断言文案迁移为家教场景。

### P1：第二批修改

- `app.py`
  - FastAPI title、description、启动日志中的系统名称；注意不要改变路由和生命周期逻辑。
- `web/templates/*.html`
  - 首页、知识库、技师状态、排班、用户行为分析页面的展示文案。
- `web/routes.py`
  - 页面标题、模板上下文、日志文案。
- `api/technician.py`
  - 对外文档 tags、summary、错误信息从技师改为老师。
- `api/appointment.py`
  - 对外文档和 response message 从按摩预约改为试听课预约/正式排课。
- `api/user_behavior_analysis.py`
  - 对外文案从用户行为分析迁移为学习需求分析。
- `api/core/response_models.py`
  - 注释和接口说明迁移；字段名暂时保留。

### P2：后续评估

- `db/models.py`
- `db/db_router.py`
- `db/base/*.py`
- `db/repositories/*.py`
- `services/appointment_service.py`
- `services/user_behavior_service.py`
- `agents/appointment/technician_finder.py`
- `agents/appointment/appointment_processor.py`
- `agents/appointment/appointment_database.py`
- `agents/user_behavior/*.py`
- API 路由路径 `/api/technicians`、`/api/appointment`
- 数据库文件名 `smart_appointment.db`

P2 涉及内部模型、Repository、排课可用性、用户行为统计和预约状态机。直接改名或改字段会造成连锁失败，建议等家教场景 MVP 跑通后再决定是否重构。

## 4. 文件风险分级

### 低风险文件

- `docs/*.md`
- `README.md`
- `web/templates/*.html` 中纯展示文案
- `agents/consultant/prompt_builder.py`
- `agents/task_classification/unrelated_handler.py`
- `tests/*.py` 中测试输入和断言文案

低风险原因：主要影响说明、展示、prompt 语义和测试语义，不直接改变数据库结构或 API 调用链。

### 中风险文件

- `app.py`
- `services/knowledge_service.py`
- `services/technician_service.py`
- `agents/task_classification/task_classifier.py`
- `agents/appointment/input_parser.py`
- `agents/appointment/message_builder.py`
- `api/*.py`
- `web/routes.py`

中风险原因：会影响启动初始化、默认数据库内容、LLM 输出格式、接口文档或页面渲染，但通常不需要改表结构。

### 高风险文件

- `db/models.py`
- `db/db_router.py`
- `db/base/*.py`
- `db/repositories/*.py`
- `services/appointment_service.py`
- `services/user_behavior_service.py`
- `agents/appointment/technician_finder.py`
- `agents/appointment/appointment_processor.py`
- `agents/appointment/appointment_database.py`

高风险原因：这些文件绑定 SQLite 表、Repository、预约状态、老师可用性和统计逻辑。当前阶段不建议修改。

## 5. 迁移类型拆分

| 类型 | 主要内容 | 代表文件 | 处理策略 |
| --- | --- | --- | --- |
| 文案迁移 | 项目名、页面标题、按钮、提示语、接口说明、错误消息 | `README.md`、`app.py`、`web/templates/*.html`、`api/*.py` | 先改对外可见内容，内部变量暂时不动。 |
| 数据迁移 | 默认知识库、默认老师、课程/学科、老师风格、学生需求样例 | `services/knowledge_service.py`、`services/technician_service.py` | 保留字段结构，替换初始化内容。 |
| Agent prompt 迁移 | 任务分类、课程咨询、试听课预约、学习需求分析、无关问题处理 | `agents/**/*.py` 中 prompt 相关文件 | 不改 Agent 编排结构，只改系统提示词和抽取语义。 |
| 测试用例迁移 | 输入语句、断言类别、期望回复、业务样例 | `tests/*.py` | 用家教场景替换按摩场景，保留测试结构。 |
| 内部命名迁移 | `technician`、表名、路由路径、Repository 命名 | `db/*`、`services/*`、`api/*` | 当前不做，MVP 稳定后评估。 |

## 6. 不建议当前阶段修改的内容

- 不重命名 Python 包、文件名、类名和函数名。
- 不重命名数据库表和字段。
- 不修改 API 路由路径。
- 不修改数据库初始化和连接方式。
- 不通过核心代码绕过模型凭据或 embedding 配置问题。
- 不做跨项目整合。
- 不引入新框架或替换 LangChain、FAISS、SQLite。
- 不做大规模架构重构。

## 7. 推荐执行顺序

1. 第 1.5 阶段：落盘领域映射、迁移计划和基线报告。
2. 第 2 阶段：迁移 README、应用标题、默认知识库和默认老师数据。
3. 第 3 阶段：迁移课程咨询、任务分类、试听课预约和学习需求分析 prompt。
4. 第 4 阶段：迁移前端页面文案、API 文档文案和错误提示。
5. 第 5 阶段：迁移测试用例，形成家教场景回归测试。
6. 第 6 阶段：运行 FastAPI smoke test、pytest、关键接口手工验证。
7. 第 7 阶段：评估是否重构内部命名和数据库模型。

## 8. 每阶段验收标准

### 第 1.5 阶段：文档落地 + 基线记录

- `docs/DOMAIN_MIGRATION_MAP.md` 已包含完整领域映射、老师风格和学生需求样例。
- `docs/MIGRATION_PLAN.md` 已包含优先级、风险分级、迁移类型、推荐顺序和验收标准。
- `docs/BASELINE_REPORT.md` 已记录当前启动命令、测试命令、环境状态、报错和暂缓修复项。
- 核心业务代码没有修改。

### 第 2 阶段：对外文案和默认数据迁移

- README 和应用标题体现“AI 家教培训机构智能咨询与排课系统”。
- 默认知识库不再以按摩服务为主，改为课程体系、收费规则、老师介绍、试听课规则、退费规则、上课须知。
- 默认技师数据对外呈现为老师数据，包含科目、年级、教学风格。
- FastAPI 至少能完成导入；完整启动结果有记录。

### 第 3 阶段：Agent prompt 迁移

- 课程咨询 Agent 能回答课程体系、收费、老师介绍、试听规则。
- 预约 Agent 能围绕学生年级、薄弱科目、学习目标、老师偏好、可上课时间进行追问。
- 用户行为 Agent 对外语义变为学习需求分析。
- 任务分类 Agent 能区分课程咨询、试听预约、正式排课、学习需求分析和无关问题。

### 第 4 阶段：页面和 API 文档迁移

- 首页、知识库、老师列表、老师课表、学习需求分析页面不再出现按摩门店主文案。
- API 文档 summary、tag、response message 对外体现老师、课程、试听课和排课。
- 字段名如 `technician_id` 可暂时保留，但说明文案要解释为老师。

### 第 5 阶段：测试用例迁移

- 测试输入覆盖数学基础薄弱、英语听说困难、作文不会写、物理概念不清、考前提分、学习习惯督促。
- `pytest` 至少能完成收集；若失败，失败原因被记录。
- 任务分类、咨询、预约、学习需求分析测试均使用家教场景语料。

### 第 6 阶段：可运行 MVP 验收

- FastAPI 服务可访问。
- `/docs` 可打开。
- 首页可进行课程咨询或试听课预约的基础交互。
- 知识库检索能返回课程相关内容。
- 老师/课表页面对外文案一致。
- 已知依赖、模型凭据或 embedding 问题有明确记录，不通过核心业务代码硬绕过。

### 第 7 阶段：内部命名重构评估

- 根据 MVP 稳定性决定是否把 `technician`、`appointment` 等内部命名迁移为 teacher/course schedule。
- 若重构，必须配套数据库迁移、接口兼容策略和回归测试。
