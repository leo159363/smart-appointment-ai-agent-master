# 项目学习指南 — AI 家教培训机构智能咨询与排课系统

> 从基础到进阶，按 4 个阶段组织。每个知识点标注了**必读源码**和**对应面试题**。

---

## 学习路线图

```
第一阶段（基础）   → 能讲清楚项目是什么、怎么启动、有哪些页面
第二阶段（核心）   → 能讲清楚多 Agent 怎么协作、RAG 怎么检索、预约怎么排课
第三阶段（进阶）   → 能讲清楚 Modular RAG MCP 架构、测试基线、领域迁移策略
第四阶段（实战）   → 能定位缺陷、解释最新改动、讨论后续规划
```

---

# 第一阶段：基础认知

学习目标：**用 3 分钟介绍这个项目，知道怎么启动它。**

## 1.1 项目是什么

**必读文件**：`README.md`（5分钟）

**核心概念**：
- 这是一个 AI 家教培训机构智能咨询与排课系统
- 从按摩门店预约系统迁移而来，已完成为期 6 轮的质量迭代
- MVP 定位：可演示、可运行、不追求生产级

**自检问题**：能用一句话说清楚这个项目解决什么问题吗？
> "它让家长通过聊天的方式咨询课程、匹配老师、预约试听课和安排正式排课，背后由 4 个 AI Agent 协作完成。"

## 1.2 启动项目

**必读文件**：`app.py`, `.env.example`

**关键命令**：
```powershell
.\.venv\Scripts\Activate.ps1                # 激活虚拟环境
.\.venv\Scripts\python.exe scripts\reset_demo_data.py  # 重置演示数据
.\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000  # 启动
```

**系统启动做了三件事**（`initialize_system()`）：
1. 初始化知识库 → 8 条课程知识 + FAISS 索引
2. 初始化老师数据 → 10 位默认老师
3. 启动推荐调度器 → 定时任务

**自检问题**：不看文档，能说出启动命令吗？

## 1.3 有哪些页面和 API

**页面**（6个）：
| 路径 | 功能 |
|---|---|
| `/` | 首页聊天 — 核心交互入口 |
| `/docs` | Swagger API 文档 |
| `/knowledge` | 知识库管理 |
| `/technician` | 老师状态（10位老师） |
| `/technician_schedule` | 老师课表 |
| `/user_behavior_analysis` | 学习需求分析 |
| `/admin` | 系统管理仪表板 |

**API**（7组）：`/api/knowledge`, `/api/technicians`, `/api/appointment`, `/api/consultation`, `/api/task`, `/api/user-behavior`

**自检问题**：打开浏览器，能自己点一遍所有页面吗？

## 1.4 核心概念速览

**必读文件**：`config/constants.py`

| 概念 | 含义 |
|---|---|
| `StateEnum` | 对话状态：CLASSIFY → APPOINTMENT 或 CONSULT → 回到 CLASSIFY |
| `SharedState` | 在多 Agent 间共享当前状态的简单对象 |
| `technician` | 内部字段名 = 老师（兼容保留） |
| `appointment` | 内部字段名 = 预约/排课（兼容保留） |
| `project` | 内部字段名 = 课程/学科（兼容保留） |
| `strength` | 内部字段名 = 教学方向/风格（兼容保留） |

**自检问题**：为什么内部还叫 `technician` 不改成 `teacher`？

---

# 第二阶段：核心架构

学习目标：**理解一条消息从头到尾经过了哪些环节。**

## 2.1 六层架构

**必读文件**：`app.py`, `web/routes.py`, `api/chat_handler.py`

```
Web 前端 (Jinja2 + vanilla JS)
  → web/routes.py      — 页面路由 + /chat/stream 入口
  → api/chat_handler.py — ChatHandler 单例 Agent 管理
  → agents/             — 4 个 Agent 协作
  → services/           — 知识库/老师/预约/Embedding
  → db/ + SQLite        — 数据持久化
```

**自检问题**：能画出这个 6 层架构图吗？

## 2.2 一条消息的完整旅程

**必读文件**：`agents/task_classification_agent.py`, `agents/task_classification/task_classifier.py`

```
用户发 "初中数学怎么收费？"
  ↓
ChatRequest → web/routes.py → /chat/stream
  ↓
chat_handler.ProcessUserInput_stream(user_input, user_id="小明妈妈")
  ↓
TaskClassificationAgent.classify_task_stream()
  ↓
TaskClassifier (LLM prompt) → "query"
  ↓
AgentRouter.route_to_consultation()
  ↓
ConsultantAgent.consult_stream()
  ├─ KnowledgeRetriever.search_knowledge()
  │   ├─ primary: RagMcpClient → Modular RAG MCP
  │   └─ fallback: KnowledgeService.search() → FAISS
  └─ ResponseGenerator → LLM 生成回答
  ↓
流式返回: [THOUGHT]...[REPLY][咨询机器人]您好！关于初中数学的收费...
```

**自检问题**：如果用户说"我想预约试听课"，路径有什么不同？

## 2.3 四个 Agent 的分工

**必读文件**：`agents/task_classification_agent.py`, `agents/consultant_agent.py`, `agents/appointment_agent.py`, `agents/user_behavior_agent.py`

| Agent | 文件 | 做什么 | 关键子模块 |
|---|---|---|---|
| 任务分类 | `task_classification_agent.py` | 判断意图，分发任务 | `TaskClassifier`, `AgentRouter`, `StateManager` |
| 课程咨询 | `consultant_agent.py` | RAG 检索 → LLM 回答 | `KnowledgeRetriever`, `ResponseGenerator` |
| 预约排课 | `appointment_agent.py` | 信息抽取→追问→匹配→预约 | `InputParser`, `TechnicianFinder`, `AppointmentProcessor` |
| 学习分析 | `user_behavior_agent.py` | 行为记录→偏好分析→回访提醒 | `BehaviorRecorder`, `PatternAnalyzer` |

**为什么拆成 4 个而不是 1 个大 Agent？**
- 单一 Agent prompt 太长，分类 + 咨询 + 预约全塞一起会降低质量
- 不同任务需要不同的 LLM 参数（咨询 temperature=0.3，预约更精确）
- 预约流程有自己的状态机，不能和咨询混在一起

**自检问题**：AgentRouter 收到 "appointment" 会调用哪个 Agent？收到 "query" 呢？

## 2.4 RAG 知识库怎么工作

**必读文件**：`services/knowledge_service.py`, `agents/consultant/knowledge_retriever.py`

```
知识库有两层：

第一层（默认，优先）：Modular RAG MCP Server
  └─ 通过 mcp_stdio 启动子进程 → 调 query_knowledge_hub
  └─ 检索 tutoring_course_kb 集合 → 返回结果
  └─ 失败/超时 → 自动降级 ↓

第二层（本地 fallback）：SQLite + FAISS
  └─ 8 条课程知识文档 (knowledge_documents 表)
  └─ embed_input() 生成向量
  └─ FAISS IndexFlatIP 内积相似度搜索
  └─ 返回 top_k 结果
```

**3 种模式**：`RAG_MCP_MODE=primary`（默认）/ `shadow` / `local`

**自检问题**：如果 Modular RAG 服务挂了，用户还能正常咨询吗？

## 2.5 预约排课的完整流程

**必读文件**：`agents/appointment_agent.py`, `agents/appointment/input_parser.py`, `agents/appointment/appointment_processor.py`

```
用户: "预约周六下午3点初中数学试听课，90分钟"
  ↓
InputParser (LLM 提取 JSON):
  {start_time: "2026-06-13 15:00", duration: "90", project: "初中数学",
   appointment_type: "trial", info_complete: true}
  ↓
AppointmentProcessor.update_history_from_data()
  ↓
TechnicianFinder.find_and_match_technician()
  1. 获取所有老师
  2. filter_technicians_by_gender(不限)
  3. filter_technicians_by_preference(embedding 相似度)
  4. find_available_technician(时间可用)
  ↓
AppointmentDatabase.save_appointment()
  ↓
成功消息: "已为您预约试听课，老师：张伟。试听结束后老师会给出学习建议..."
```

**关键细节**：
- `start_time`, `project`, `duration` 是必填的
- `gender`（老师性别偏好）不是必填，不填就匹配任意合适老师
- 试听课和正式课有不同的成功消息（最新改动）
- 如果指定老师没空，系统会推荐相似老师

**自检问题**：用户说"我要上课"不提供细节，Agent 怎么处理？

---

# 第三阶段：进阶理解

学习目标：**深入理解架构决策、迁移策略、质量保障。**

## 3.1 Modular RAG MCP 双层架构

**必读文件**：`config/rag_mcp_config.py`, `services/rag_mcp_client.py`, `services/rag_eval_logger.py`

**关键代码路径**：
```python
# knowledge_retriever.py
def search_knowledge(self, query, top_k=3):
    if self.rag_mcp_config.is_primary:     # 默认走这
        return await self._search_primary(query, top_k)
    # local/shadow 模式走本地
    ...

async def _search_primary(self, query, top_k):
    modular_result = await self._query_modular(query, top_k)
    if modular_result["ok"] and modular_result["documents"]:
        return modular_docs       # ← Modular 成功
    # fallback 到本地 FAISS
    return await self._search_local(query, top_k)
```

**为什么这样设计？**
- Modular RAG 有更好的检索质量（BM25 + embedding 混合 + rerank）
- 但它是一个独立的子进程，有启动开销和可用性风险
- 本地 FAISS 作为 fallback 保证咨询链路不中断

**自检问题**：`RAG_MCP_MODE=primary` 但 `RAG_MCP_TRANSPORT` 没配置，会发生什么？

## 3.2 领域迁移策略

**必读文件**：`docs/DOMAIN_MIGRATION_MAP.md`, `docs/MIGRATION_PLAN.md`

**迁移三原则**：
1. 对外优先：先改 README、Agent prompt、API 文档 → 再改页面 → 最后评估 DB 字段
2. 风险分级：P0（低风险文案）→ P1（中风险 prompt/页面）→ P2（高风险 DB/路由）
3. 不全局替换：`technician` 贯穿 15+ 个文件，直接重命名会连锁崩溃

**六轮迭代记录**：
| 轮次 | 改动 |
|---|---|
| 1 | RAG 文档修正：default `local` → `primary` |
| 2 | 用户区分机制：localStorage + 昵称 |
| 3 | 旧域残留清理：massage/推拿/技师 → 试听课/家教/老师 |
| 4 | 注释和 UI 优化：去性别暴露、旧域名注释 |
| 5 | Bug 修复：admin 模板、embedding 脱敏、top_k |
| 6 | 试听课/正式课区分 |

**自检问题**：如果要你继续做第 7 轮迭代，你会做什么？

## 3.3 测试基线与质量体系

**必读文件**：`docs/BASELINE_REPORT.md`, `tests/`

**测试基线**：
```powershell
.\.venv\Scripts\python.exe -c "import app"           # Smoke test
.\.venv\Scripts\python.exe -m pytest --collect-only   # 52 tests
.\.venv\Scripts\python.exe -m pytest tests/test_task_classification_agent.py -q
```

**A/B/C/D/E 风险分类**：
| 分类 | 含义 | 例子 |
|---|---|---|
| A | LLM 外部依赖 | 任务分类测试因 API 连接失败 |
| B | 测试与实现不一致 | 测试期望旧场景输出但代码已迁移 |
| C | SQLite 数据问题 | 演示数据字段不匹配 |
| D | 旧场景文案残留 | 页面出现"按摩""技师" |
| E | 真实功能阻塞 | admin 模板缺失导致 500 |

**哲学**：先基线 → 分类记录 → 阶段修复 → 不盲目追求全绿

**自检问题**：有一个测试因为 LLM API Key 过期而失败，你该把它分到哪一类？

## 3.4 流式标记协议

**理解 `[THOUGHT]` / `[REPLY]` / `[ERROR]`**

所有 Agent 响应通过 async generator 流式返回，前端根据标记渲染不同样式：

| 标记 | 含义 | 前端样式 |
|---|---|---|
| `[THOUGHT][agent_name]` | Agent 内部思考 | 黄色气泡 |
| `[REPLY][agent_name]` | 最终回复 | 白色主体 |
| `[ERROR]` | 错误 | 红色 |

**自检问题**：为什么预约 Agent 不在用户聊天窗口显示 `[THOUGHT]` 中出现的内部 JSON？

---

# 第四阶段：实战能力

学习目标：**能定位缺陷、解释改动、参与设计讨论。**

## 4.1 用户身份全链路

**关键文件**：`web/templates/index.html`（JS）, `web/routes.py`, `api/chat_handler.py`

这是第 2 轮迭代的核心改动。完整链路：

```
localStorage.getItem('tutoring_user_info')
  → {user_id: "user_a1b2", nickname: "小明妈妈"}
  → getDisplayUserId() → "小明妈妈"
  → fetch('/chat/stream', {message, user_id: "小明妈妈"})
  → web/routes.py: ProcessUserInput_stream(message, user_id="小明妈妈")
  → chat_handler.py: consultant_agent.user_id = "小明妈妈"
  → behavior_recorder: user_id="小明妈妈" 写入 DB
  → /api/user-behavior/analysis?user_id=小明妈妈 → 只看小明妈妈的数据
```

**自检问题**：如果用户清除了浏览器缓存，之前的数据还在吗？

## 4.2 实际修复过的 10 个缺陷

| # | 缺陷 | 类型 | 修复文件 |
|---|---|---|---|
| 1 | `'massage'` 硬编码在预约记录中 | D | `appointment_database.py` |
| 2 | `"推拿服务"` 作为默认业务上下文 | D | `task_classification_agent.py` |
| 3 | admin 模板缺失导致 500 | E | 新建 `admin_dashboard.html` |
| 4 | 知识 API 返回完整 embedding 向量 | 性能 | `api/knowledge.py` |
| 5 | SearchRequest 不支持 top_k | 功能 | `api/knowledge.py` |
| 6 | add_knowledge 调用不存在的函数 | E | `api/knowledge.py` |
| 7 | 重复 `from datetime import datetime` | C | `db/models.py` |
| 8 | 预约成功消息暴露"性别" | D | `message_builder.py` |
| 9 | preference_manager 注释"技师/力气" | D | `preference_manager.py` |
| 10 | 所有用户共享 `default_user` | E | 全链路 11 个文件 |

**自检问题**：能说出至少 5 个你亲手修过的缺陷吗？

## 4.3 代码阅读速查表

**如果你要快速定位一个功能，看这些文件**：

| 想了解什么 | 看哪个文件 |
|---|---|
| 系统怎么启动的 | `app.py` |
| 消息怎么分发到 Agent | `api/chat_handler.py` → `agents/task_classification_agent.py` |
| 知识库怎么检索 | `agents/consultant/knowledge_retriever.py` → `services/knowledge_service.py` |
| Modular RAG 怎么调用 | `services/rag_mcp_client.py` |
| 预约信息怎么抽取 | `agents/appointment/input_parser.py` |
| 老师怎么匹配 | `agents/appointment/technician_finder.py` |
| 用户消息怎么构建 | `agents/appointment/message_builder.py` |
| 数据存在哪些表 | `db/models.py` |
| 演示数据怎么造 | `scripts/reset_demo_data.py` |
| RAG 模式怎么配置 | `config/rag_mcp_config.py` |
| 前端怎么发请求 | `web/templates/index.html`（找 fetch） |
| 环境变量有哪些 | `.env.example` |

## 4.4 当前架构缺口（知道什么还没做）

| 缺口 | 优先级 |
|---|---|
| 老师模型没有 `subject`/`grade_level` 结构化字段 | 高 |
| 预约没有取消/改约功能 | 高 |
| 推荐引擎是空壳（永远返回空列表） | 中 |
| 没有对话历史持久化 | 中 |
| 没有 fake/mock LLM provider | 中 |
| 老师课表只能看不能手动编辑 | 低 |
| 知识库没有 JSON 批量导入 | 低 |
| 没有 Docker 部署 | 低 |

---

# 学习检查清单

完成以下所有项，你就能自信地面试：

- [ ] 能用 3 分钟介绍这个项目（业务+架构+边界）
- [ ] 能说出 4 个 Agent 的名字和职责
- [ ] 能画出"一条消息从输入到回复"的完整链路
- [ ] 能解释为什么保留 `technician` 字段
- [ ] 能说出 RAG 两层架构：Modular RAG MCP（primary）+ FAISS（fallback）
- [ ] 能说出试听课和正式课的区别
- [ ] 能说出至少 5 个你修过的缺陷
- [ ] 能说出 A/B/C/D/E 风险分类
- [ ] 能说出 52 个测试中哪些会失败以及为什么
- [ ] 能说出至少 3 个下一阶段应该做的改进
- [ ] 能独立启动项目并走通咨询+预约流程
