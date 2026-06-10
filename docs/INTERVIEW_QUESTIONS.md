# 面试题汇总 — AI 家教培训机构智能咨询与排课系统

> 共 20 题，覆盖项目综述、架构、多 Agent、RAG、预约排课、测试质量、工程化 7 个主题。

---

## 一、项目综述（2 题）

### RQ01 | 请用 2-3 分钟介绍这个项目

**考点**：能否讲清业务场景 + 架构 + MVP 边界

**参考答案要点**：
- **一句话**：AI 家教培训机构智能咨询与排课系统，基于 FastAPI + 多 Agent + RAG 知识库，支持课程咨询、老师匹配、试听课预约、正式排课和学习需求分析
- **业务场景**：家长/学生在首页输入问题 → 系统判断是咨询还是预约 → 咨询走 RAG 检索课程知识 → 预约走信息抽取 + 老师匹配 + 排课流程
- **技术架构**：6 层设计 — Web(Jinja2) → FastAPI Routes → API 层 → Agent 层(多Agent路由) → Service 层(FAISS RAG) → Data 层(SQLite+FAISS)
- **MVP 边界**：单用户、无登录、内部保留 `technician` 兼容字段、Modular RAG MCP 默认 primary 主检索
- **演示价值**：52 个测试、6 个页面可访问、端到端链路完整

**源码锚点**：`app.py`, `README.md`, `docs/ARCHITECTURE.md`

---

### RQ02 | 为什么从预约系统迁移成家教培训机构场景？为什么保留 `technician` 字段？

**考点**：领域迁移的工程决策能力

**参考答案要点**：
- **迁移动机**：原系统是按摩门店预约系统，场景不匹配。家教培训是自己熟悉的领域，迁移后能展示真实的业务理解
- **迁移策略**：分 P0/P1/P2 三批修改，先改对外文案和 Agent prompt，再改页面和 API 文档，最后评估是否改数据库字段名
- **保留 `technician` 的原因**：这个字段贯穿 DB 模型、Repository、Service、API 路由、Agent 全链路。直接重命名会破坏可运行性。MVP 阶段先在代码注释和文档中标注"兼容保留"，对外展示用"老师"
- **同样保留的字段**：`appointment`（预约/排课）、`service_type`（课程/学科）、`project`（学科）、`strength`（教学方向）

**源码锚点**：`docs/DOMAIN_MIGRATION_MAP.md`, `docs/MIGRATION_PLAN.md`, `db/models.py`

---

## 二、架构与后端（3 题）

### RQ03 | 一次首页输入会经过哪些层？核心模块有哪些？

**考点**：理解完整请求链路

**参考答案要点**：
```
用户输入 "初中数学怎么收费？"
  → web/routes.py: /chat/stream 端点接收 ChatRequest
  → api/chat_handler.py: ProcessUserInput_stream()
  → agents/task_classification_agent.py: classify_task_stream()
    → TaskClassifier (LLM prompt) → 分类为 "query"
    → AgentRouter → route_to_consultation()
    → ConsultantAgent.consult_stream()
      → KnowledgeRetriever.search_knowledge()
        → 默认 primary: RagMcpClient (MCP stdio) → Modular RAG MCP
        → fallback: KnowledgeService.search() → FAISS 本地检索
      → ResponseGenerator → LLM 生成回答 → 流式返回
```

**核心模块**：
- Web 层：Jinja2 模板渲染 + 流式聊天
- API 层：7 组 REST 接口（knowledge, technician, appointment, consultation, task, user-behavior）
- Agent 层：4 个 Agent（分类/咨询/预约/学习需求分析）
- Service 层：知识库/老师/预约/用户行为/推荐/Embedding
- Data 层：SQLite + FAISS + Modular RAG MCP

**源码锚点**：`app.py`, `web/routes.py`, `api/chat_handler.py`, `agents/`

---

### RQ14 | FastAPI 启动流程是什么？有哪些页面和 API 入口？

**考点**：后端基础

**参考答案要点**：
- `app.py` → `create_app()` 创建 FastAPI 实例
- 注册 CORS 中间件、异常处理器、7 组 API 路由 + Web 路由
- `startup_event` → `initialize_system()` 执行三件事：
  1. `KnowledgeService.initialize()` — 从 SQLite 加载 8 条知识，构建 FAISS 索引
  2. `TechnicianService.initialize_default_technicians()` — 插入 10 位默认老师
  3. `RecommendationService.start_scheduler()` — 启动定时推荐任务
- 页面入口：`/`, `/knowledge`, `/technician`, `/technician_schedule`, `/user_behavior_analysis`, `/admin`
- API 文档：`/docs` (Swagger UI)
- uvicorn 启动：`uvicorn app:app --host 127.0.0.1 --port 8000`

**源码锚点**：`app.py:68-108`

---

### RQ05 | 任务分类 Agent 失败时为什么会影响测试？怎么分类这个失败？

**考点**：测试基线 + 风险分类

**参考答案要点**：
- 任务分类 Agent 依赖真实 LLM（DeepSeek/Qwen 等）进行分类
- 测试环境无 LLM 连接或 API Key 无效时，`TaskClassifier.classify_task()` 会失败
- 失败分类是 **A 类**（LLM/外部依赖失败），不是代码 bug
- A/B/C/D/E 风险分类体系：
  - A：LLM/外部依赖失败
  - B：测试与实现不一致
  - C：SQLite 数据处理问题
  - D：页面/API 旧场景文案残留
  - E：真实功能阻塞
- 策略：先建立基线、分类记录、不盲目修代码追求全绿

**源码锚点**：`tests/test_task_classification_agent.py`, `docs/BASELINE_REPORT.md`

---

## 三、多 Agent 系统（3 题）

### RQ04 | 多 Agent 是怎么分工的？为什么不做成一个大 Agent？

**考点**：多 Agent 设计理念

**参考答案要点**：
- **4 个 Agent**：
  1. `TaskClassificationAgent` — 入口，用 LLM 分类用户意图（appointment/query/other）
  2. `ConsultantAgent` — RAG 知识库问答（课程、收费、老师介绍）
  3. `AppointmentAgent` — 信息抽取 → 缺失追问 → 老师匹配 → 预约确认
  4. `UserBehaviorAgent` — 行为记录 → 偏好分析 → 回访提醒
- **为什么拆分**：
  - 单一 Agent 上下文膨胀，prompt 太长导致分类和回答质量都下降
  - 不同任务需要不同的 LLM 参数（咨询用 temperature=0.3，预约用更精确的参数）
  - 状态隔离：预约流程有自己的状态机，不能和咨询流程混在一起
- **共享状态**：`SharedState` + `StateEnum` (CLASSIFY → APPOINTMENT/CONSULT → CLASSIFY)
- **单例模式**：4 个 Agent 在 `chat_handler.py` 中只创建一次，全请求复用

**源码锚点**：`agents/task_classification_agent.py`, `api/chat_handler.py`, `config/constants.py`

---

### RQ06 | 预约/排课 Agent 如何处理缺失信息？试听课和正式课有什么区别？

**考点**：预约状态机 + 最近新增的试听/正式课区分

**参考答案要点**：
- **信息抽取**：`InputParser` 用 LLM prompt 从自然语言提取 JSON（start_time, duration, project, preference, appointment_type 等）
- **缺失信息追问**：`MessageBuilder` 将内部字段名映射为中文业务字段，逐一追问
- **必填字段**：start_time, project, duration；gender 和 preference 不是必填
- **试听课 vs 正式课**（最新改动）：
  - `appointment_type` 字段：trial（试听课）/ formal（正式课）
  - 通过 LLM 抽取 + 关键词规则双重检测
  - 成功消息区分：试听课提示"试听反馈→正式方案"，正式课提示"固定上课时间"
- **不暴露内部字段**：duration/gender 是内部字段，问用户时应该说"课程时长"/"老师性别偏好"

**源码锚点**：`agents/appointment/input_parser.py`, `agents/appointment/message_builder.py`, `agents/appointment_agent.py:_normalize_appointment_type`

---

### RQ07 | 老师匹配现在怎么做？Embedding 在哪里参与？

**考点**：TechnicianFinder 内部机制

**参考答案要点**：
- **匹配流程**：
  1. `TechnicianFinder.find_and_match_technician()` 获取所有老师
  2. `filter_technicians_by_gender()` — 按性别筛选
  3. `filter_technicians_by_preference()` — 按老师风格做 embedding 相似度
  4. `find_available_technician()` — 按时间可用性最终匹配
- **Embedding 参与点**：`filter_technicians_by_preference()` 中，将用户偏好文本和老师 `strength` 字段文本分别 embedding，用 FAISS `IndexFlatL2` 找最近邻
- **局限**：`strength` 字段把所有信息（学科、年级、风格）混在一起，只能做语义匹配，不能精确筛选。下一步应加 `subject` 和 `grade_level` 列

**源码锚点**：`agents/appointment/technician_finder.py`, `services/text_embedding.py:find_best_match_indices`

---

## 四、RAG 知识库（3 题）

### RQ08 | RAG 课程知识库如何存储和检索？

**考点**：RAG 全链路

**参考答案要点**：
- **存储层**：SQLite `knowledge_documents` 表（content, category, keywords, embedding JSON）
- **索引层**：`KnowledgeService._build_vector_index()` 用 FAISS `IndexFlatIP`（内积相似度）构建向量索引
- **检索流程**：
  1. 用户 query → `embed_input()` 生成 embedding
  2. FAISS `index.search()` 向量检索
  3. 可选 category 过滤
  4. 返回 top_k 结果
- **内容**：8 条默认知识覆盖咨询时间、课程体系、老师介绍、校区/线上、课程介绍、教学质量、排课规则、课时包/收费
- **兜底**：`ResponseGenerator` 对收费/课时包问题有规则型 fallback（试听课、10/20课时包）

**源码锚点**：`services/knowledge_service.py`, `db/models.py`, `agents/consultant/response_generator.py`

---

### RQ09 | RAG 检索质量你会怎么评估？

**考点**：RAG 评估体系设计

**参考答案要点**：
- **离线评估指标**：Hit@K, MRR, Context Precision, Answer Faithfulness
- **业务关键点覆盖**：课程体系、收费规则、试听规则、老师信息、排课规则等
- **Golden Set**：`tests/fixtures/tutoring_rag_golden_set.json` 已有 10 条测试用例
- **Modular RAG Shadow 对比**：设置 `RAG_MCP_MODE=shadow`，后台调用 Modular RAG 并记录对比日志到 `logs/rag_eval/`
- **下一步**：自动化评估脚本 + 更大规模 golden set

**源码锚点**：`tests/fixtures/tutoring_rag_golden_set.json`, `services/rag_eval_logger.py`

---

### RQ10 | Modular RAG MCP 和本地 FAISS 什么关系？默认走哪个？

**考点**：双层 RAG 架构

**参考答案要点**：
- **三层模式**：
  - `primary`（默认）：优先 Modular RAG MCP → 失败 fallback 本地 FAISS
  - `shadow`：本地 FAISS 给用户，后台旁路调 Modular 写对比日志
  - `local`：纯本地 FAISS，不调 Modular
- **Modular RAG MCP 客户端**：`RagMcpClient` 支持三种 transport — `mcp_stdio`（启动子进程）、HTTP、CLI
- **默认是 primary**：代码中 `DEFAULT_RAG_MCP_MODE = "primary"`
- **Fallback 逻辑**：Modular 不可用/超时/返回空 → 自动降级本地 FAISS → jsonl 日志记录 `final_source`
- **关键设计**：Modular RAG 是主检索源，但不是硬替换；本地 FAISS 保留保证可用性

**源码锚点**：`config/rag_mcp_config.py`, `agents/consultant/knowledge_retriever.py`, `services/rag_mcp_client.py`

---

## 五、测试与质量（4 题）

### RQ15 | 如何向面试官解释 pytest 不是全绿？

**考点**：质量表达 + 风险意识

**参考答案要点**：
- 当前 52 个测试可 collect，但部分依赖真实 LLM 的测试会因 API 连接失败
- 这是 **A 类已知问题**，不是代码 bug
- 质量策略：先基线 → 分阶段迁移 → 分类记录 → 不盲目追求全绿
- 后续引入 fake/mock LLM provider 就能让 CI 稳定跑全量

**源码锚点**：`pytest.ini`, `tests/`, `docs/BASELINE_REPORT.md`

---

### RQ12 | 你如何发现并修复旧场景文案残留？

**考点**：缺陷定位方法

**参考答案要点**：
- **方法**：
  1. 关键词扫描：全局搜索"按摩、推拿、技师、门店、顾客、massage"等旧域名词
  2. 页面验收：逐个打开 6 个页面，检查展示文案
  3. API 返回检查：确认 response message 不出现旧场景
  4. SQLite 演示数据检查：确认知识库和老师数据已迁移
- **实际修复案例**：
  - `appointment_database.py`: `'project': 'massage'` → `'试听课'`
  - `task_classification_agent.py`: `"推拿服务"` → `"家教课程咨询与排课服务"`
  - `message_builder.py`: 去掉用户消息中的"性别"暴露
  - `preference_manager.py`: "技师偏好/力气大小" → "老师偏好/教学风格"
- 分类为 **D 类问题**（页面/API/演示数据旧场景文案残留）

**源码锚点**：`docs/DOMAIN_MIGRATION_MAP.md`, `agents/appointment/message_builder.py`

---

### RQ13 | `[object Object]`、`default_user`、字段暴露分别是什么类型的问题？

**考点**：前端/体验缺陷分类

**参考答案要点**：
- `[object Object]`：前端把 JS 对象直接渲染到 HTML（应 JSON.stringify 或取属性）。D 类
- `default_user`：内部默认 user_id 直接展示在页面上，应显示用户名或隐藏。D 类
- `duration/gender` 暴露：内部字段名直接出现在用户消息中（如"课程时长60分钟"变成"duration: 60"）。已修：message_builder 维护字段映射表
- 修复后（最新改动）：前端加了 localStorage 用户昵称输入，分析页面动态显示当前用户

**源码锚点**：`web/templates/user_behavior_analysis.html`, `agents/appointment/message_builder.py`

---

### RQ16 | 后续如果做测试开发项目包装，你会补哪些测试？

**考点**：测试设计能力

**参考答案要点**：
- **Fake/Mock LLM Provider**（最优先）：让 Agent 测试在 CI 中真正运行，不依赖外部 API
- **API 自动化测试**：覆盖 knowledge CRUD、chat 基本流程、user-behavior 分析
- **Playwright 页面自动化**：6 个页面的 smoke test，聊天交互流程
- **RAG Golden Set 自动评估**：已有 `tutoring_rag_golden_set.json`，补充自动打分脚本
- **CI 增强**：把 fake LLM + API 测试 + Playwright 接入 GitHub Actions

**源码锚点**：`tests/`, `.github/workflows/ci.yml`

---

## 六、工程化（3 题）

### RQ11 | `reset_demo_data.py` 解决了什么问题？

**考点**：工程化意识

**参考答案要点**：
- 备份当前 SQLite → 清理旧数据 → 写入 8 条家教知识 + 10 位老师
- 不修改数据库 schema
- 为什么不用提交 SQLite：本地数据库含演示数据和个人配置，提交会造成冲突
- 任何时候跑这个脚本就能恢复干净的演示环境

**源码锚点**：`scripts/reset_demo_data.py`

---

### RQ17 | 用户身份是怎么区分的？没有登录系统怎么知道谁是谁？

**考点**：最新改动理解（第六轮迭代）

**参考答案要点**：
- **方案**：浏览器 localStorage + 可选昵称，无密码
- **流程**：首次访问自动生成 UUID → 用户在顶部输入昵称 → localStorage 持久化 → 每次发消息携带 user_id
- **链路**：前端 fetch → `/chat/stream` → `ProcessUserInput_stream(user_id=xxx)` → 注入 `consultant_agent.user_id` 和 `appointment_agent.user_id` → 行为记录存入 DB
- **边界**：MVP 够用，生产需加真实登录系统
- **修复了 4 处硬编码**：`behavior_recorder.py`, `user_behavior_agent.py`, `appointment_database.py`, `consultation_processor.py`

**源码锚点**：`web/templates/index.html`（localStorage JS）, `api/chat_handler.py`

---

### RQ18 | 你怎么保证代码质量和迁移一致性？

**考点**：工程实践

**参考答案要点**：
- pytest 基线：52 tests collectable
- import app smoke test
- 页面/API 手工验收清单
- 旧域关键词全局扫描（按摩/推拿/massage 等）
- A/B/C/D/E 风险分类记录
- GitHub Actions CI：import + collect-only + py_compile
- 六轮迭代，每轮 commit 有清晰的改动说明

**源码锚点**：`.github/workflows/ci.yml`, `docs/BASELINE_REPORT.md`

---

## 七、场景设计（2 题）

### RQ19 | 如果用户说"孩子数学不好"，系统应该怎么回复？

**考点**：理解咨询和预约的边界

**参考答案要点**：
- 任务分类 Agent 判断为 `query` → 路由到 ConsultantAgent
- ConsultantAgent 走 RAG 检索课程体系 → LLM 生成回答（推荐一对一数学课 + 试听课）
- 不应直接进入预约流程（信息不完整）
- 回答完咨询后，引导用户提供更多信息以进入预约

---

### RQ20 | 如果 Modular RAG MCP Server 挂了，咨询还能用吗？

**考点**：理解 fallback 机制

**参考答案要点**：
- **能用！** primary 模式下自动 fallback 到本地 FAISS
- `KnowledgeRetriever._search_primary()` 中 try/except 包裹 Modular 调用
- 异常、超时、空结果全部触发 `final_source=local_fallback`
- jsonl 日志记录 fallback 原因
- 如果需要完全不走 Modular，设 `RAG_MCP_MODE=local`

**源码锚点**：`agents/consultant/knowledge_retriever.py:_search_primary`
