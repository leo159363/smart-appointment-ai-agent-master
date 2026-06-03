# AI 家教培训机构智能咨询与排课系统

AI 家教培训机构智能咨询与排课系统是一个面向教培机构和一对一家教场景的智能咨询与预约排课项目。项目基于 FastAPI、LangChain、FAISS、SQLite 和多 Agent 协作架构，实现了任务分类、RAG 知识问答、老师智能匹配、试听课预约、正式课程排课、用户行为分析和个性化提醒等能力。

本项目的目标不是只做一个普通的课程预约表单，而是模拟家教培训机构日常运营中的高频流程：理解家长或学生是在咨询课程、询问价格、匹配老师、预约试听课，还是需要正式排课；结合学生年级、薄弱科目、学习目标、可上课时间和老师风格偏好，辅助完成咨询、匹配和排课。

> 当前阶段只完成对外文案和默认数据迁移，内部包名、类名、路由路径和字段名仍可能保留原项目中的 `technician`、`appointment`、`service_type` 等命名。不要把这些内部命名理解为已经完成重构。

## 项目背景

我本人是学生，最近在教培机构做一对一家教兼职，对家教机构的真实业务更熟悉。家教培训机构在日常运营中需要处理大量重复但细节复杂的问题，例如：

- 家长咨询课程体系、收费规则、试听课安排和退费规则。
- 学生说明数学基础薄弱、英语听说困难、作文不会写、物理概念不清等学习问题。
- 课程顾问根据年级、科目、目标分数和可上课时间匹配合适老师。
- 老师需要根据课表安排试听课、正式课、改约、请假、补课和阶段反馈。
- 机构需要沉淀咨询记录、预约记录和学习需求，用于后续推荐和跟进。

因此，本项目将原始服务预约系统迁移为“AI 家教培训机构智能咨询与排课系统”，重点展示 AI Agent 在课程咨询、老师匹配、试听课预约和学习需求分析中的测试开发价值。

## 核心能力

- **智能任务分类**：自动识别用户是在课程咨询、试听课预约、正式排课、价格咨询、学习需求分析，还是提出无关问题，并将请求路由到对应 Agent。
- **多 Agent 协作**：通过任务分类 Agent、课程咨询 Agent、试听课预约/排课 Agent 和学习需求分析 Agent 分工处理复杂流程。
- **RAG 知识咨询**：使用 FAISS 向量索引检索课程体系、收费规则、老师介绍、试听课规则、退费规则和上课须知，再结合大模型生成自然语言回答。
- **老师智能匹配**：根据学生年级、薄弱科目、学习目标、老师教学风格偏好和可上课时间推荐合适老师。
- **试听课预约与正式排课**：围绕试听课预约、正式课程排课、改约、请假、补课和排课冲突处理进行流程编排。
- **用户行为分析**：记录咨询、预约和偏好信息，分析学生学习需求、薄弱科目、时间偏好和老师风格偏好。
- **个性化提醒**：在预约或排课完成后，结合课程时间、上课方式、课前准备和学习目标生成提醒。
- **Embedding 缓存优化**：通过数据库缓存和文件缓存减少重复向量计算，提高知识检索性能。
- **数据管理能力**：支持知识库、老师信息和用户行为数据的增删改查，并在数据变化后维护索引。
- **日志与兜底机制**：保留关键处理过程日志，在信息不足、模型连接失败或异常情况下提供降级处理。

## 典型业务场景

- 家长咨询：“初中数学一对一怎么安排？怎么收费？”
- 学生咨询：“我英语听说比较弱，想找互动多一点的老师。”
- 试听预约：“想预约周六下午的初中物理试听课。”
- 老师匹配：“孩子基础薄弱，希望老师耐心细致一点。”
- 正式排课：“试听后想每周三晚上和周日下午固定上课。”
- 改约请假：“这周课程想请假，能不能补到下周？”
- 学习需求分析：“孩子考前两个月想短期提分，应该怎么排课？”

## 老师和学生画像

老师样例风格包括：

- 耐心细致型
- 应试提分型
- 互动鼓励型
- 严格督促型
- 擅长基础补弱型
- 擅长拔高竞赛型

学生需求样例包括：

- 数学基础薄弱
- 英语听说困难
- 作文不会写
- 物理概念不清
- 考前短期提分
- 需要老师督促学习习惯

## 系统架构

项目采用五层架构，核心原则是：下层不反向调用上层。这样可以避免循环依赖，让业务逻辑、数据访问和接口编排保持清晰边界。

```text
Web & Application Layer
    ↓  app.py, web/：页面、路由入口、系统启动
API Layer
    ↓  api/：外部接口、请求编排、响应封装
Agents Layer
    ↓  agents/：AI Agent、任务路由、对话流程控制
Services Layer
    ↓  services/：业务逻辑、推荐算法、向量处理
DB Layer
    ↓  db/：数据模型、数据库连接、Repository
```

### 允许的调用方向

- Web 层调用 API 层
- API 层调用 Agents 层或 Services 层
- Agents 层调用 Services 层
- Services 层调用 DB 层

### 禁止的调用方式

- 下层反向调用上层
- Web 层绕过 API 直接访问 Services 或 DB
- Agents 层绕过 Services 直接访问 DB
- Services 层调用 Agents、API 或 Web

## Agent 设计

### Task Classification Agent

任务分类 Agent 是系统的主调度器，负责分析用户输入、判断任务类型，并把请求分发给合适的专业 Agent。

```text
用户输入 → 意图分析 → Agent 路由 → 响应协调
```

主要职责：

- 判断课程咨询、试听预约、正式排课、学习需求分析和无关问题。
- 维护对话状态。
- 控制不同 Agent 之间的切换。
- 处理无法分类或超出能力范围的问题。

### Consultation Agent

咨询 Agent 负责课程问答场景，使用 RAG 流程从知识库中检索相关内容，再结合大模型生成回答。

```text
任务分类 → 知识检索 → FAISS 相似度搜索 → 流式回答
```

主要职责：

- 回答课程体系、收费规则、老师介绍、试听课规则、退费规则和上课须知。
- 从知识库检索相关内容。
- 构建提示词。
- 生成自然语言回答。

### Appointment Agent

预约 Agent 负责试听课预约和正式排课相关流程，包括解析用户输入、匹配老师、检查预约信息、生成确认消息等。

```text
任务分类 → 解析学习与排课需求 → 老师匹配 → 试听课/正式排课确认
```

主要职责：

- 提取学生年级、学科、薄弱点、学习目标、上课时间和老师偏好。
- 匹配合适老师。
- 处理信息缺失时的追问。
- 生成试听课预约或正式排课结果和提醒。

### User Behavior Agent

用户行为 Agent 更偏向后台智能分析。它会根据咨询记录、预约历史和偏好数据分析学生学习需求，为后续推荐提供依据。

```text
行为记录 → 学习需求分析 → 偏好更新 → 个性化推荐
```

主要职责：

- 记录咨询、预约和学习需求行为。
- 分析薄弱科目、目标分数、时间偏好和老师风格偏好。
- 生成推荐依据。
- 支持主动反馈和个性化服务。

## 核心设计思想

### 1. 用任务分类降低系统复杂度

系统不让一个 Agent 处理所有事情，而是先判断用户意图，再分发给对应模块。这样可以让课程咨询、试听预约、正式排课和学习需求分析逻辑保持独立。

### 2. 用 RAG 解决机构知识回答

课程体系、收费规则、老师介绍、试听课规则、退费规则和上课须知适合通过知识库维护。RAG 能让回答基于可控知识来源，而不是完全依赖大模型自由生成。

### 3. 用用户行为让推荐更个性化

系统会记录学生年级、薄弱科目、学习目标、可上课时间和老师偏好。后续在推荐老师或排课方案时，可以结合历史行为，而不是每次都从零开始询问。

### 4. 用分层架构保证可维护性

Agent 负责智能流程，Service 负责业务逻辑，Repository 负责数据访问。每层只关心自己的职责，减少后期修改时的连锁影响。

### 5. 为真实教培场景预留扩展空间

项目目前以本地 SQLite 和单体服务为主，但架构上预留了模型提供商切换、MCP 外部服务接入、后台任务、缓存优化和云端部署的扩展方向。

## 架构图

![System Architecture](./architecture%20.jpg)

## 技术栈

- **后端框架**：FastAPI、Uvicorn
- **AI 框架**：LangChain
- **大模型接入**：兼容 OpenAI 格式的模型提供商，例如 Qwen、DeepSeek、Zhipu、OpenAI、Azure OpenAI
- **向量检索**：FAISS
- **数据库**：SQLite、SQLAlchemy
- **RAG 能力**：Embedding、向量索引、知识库检索、提示词构建
- **流式响应**：Python AsyncGenerator
- **前端页面**：Jinja2 模板、静态 CSS
- **外部服务扩展**：MCP，用于天气等外部信息接入
- **配置管理**：python-dotenv
- **后台任务**：schedule

## 项目结构

```text
smart-appointment-ai-agent-master/
├── agents/                         # 多 Agent 智能层
│   ├── task_classification_agent.py # 任务分类与主路由
│   ├── consultant_agent.py          # RAG 课程咨询 Agent
│   ├── appointment_agent.py         # 试听预约/排课 Agent
│   ├── user_behavior_agent.py       # 学习需求分析 Agent
│   ├── task_classification/         # 意图识别、状态管理、路由逻辑
│   ├── consultant/                  # 知识检索、提示词、回答生成
│   ├── appointment/                 # 预约解析、老师匹配、消息构建
│   └── user_behavior/               # 行为记录、偏好管理、模式分析
├── api/                             # API 编排层
│   ├── appointment.py               # 预约/排课接口
│   ├── consultation.py              # 咨询接口
│   ├── task.py                      # 任务分类接口
│   ├── chat_handler.py              # 流式聊天处理
│   ├── technician.py                # 老师管理接口，内部路径仍保留 technician 命名
│   ├── knowledge.py                 # 知识库管理接口
│   └── user_behavior_analysis.py    # 学习需求分析接口
├── services/                        # 业务逻辑层
│   ├── appointment_service.py       # 预约/排课业务逻辑
│   ├── knowledge_service.py         # 知识库管理
│   ├── recommendation_service.py    # 推荐逻辑
│   ├── technician_service.py        # 老师信息管理，内部类名仍保留 TechnicianService
│   ├── text_embedding.py            # Embedding 与向量处理
│   └── user_behavior_service.py     # 用户行为/学习需求服务
├── db/                              # 数据持久化层
│   ├── models.py                    # SQLAlchemy 模型
│   ├── db_router.py                 # 数据库路由
│   ├── local_db.py                  # 本地数据库操作
│   ├── base/                        # 数据库基础接口
│   └── repositories/                # Repository 数据访问封装
├── config/                          # 配置模块
│   ├── constants.py                 # 常量与枚举
│   ├── database.py                  # 数据库配置
│   ├── model_provider.py            # 模型与 Embedding Provider 工厂
│   ├── settings.py                  # 应用配置
│   └── time_config.py               # 时间与排班配置
├── web/                             # Web 页面层
│   ├── routes.py                    # 页面路由
│   ├── templates/                   # HTML 模板
│   └── static/                      # 静态资源
├── mcp-server/                      # MCP 外部服务扩展
├── data/                            # 数据库与缓存目录
├── docs/                            # 迁移审计和基线报告
├── tests/                           # 测试用例
├── app.py                           # 应用入口
├── requirements.txt                 # Python 依赖
├── .env.example                     # 环境变量模板
└── README.md                        # 项目说明
```

## 快速开始

### 1. 创建虚拟环境

```bash
python -m venv .venv
```

Windows PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
```

Windows CMD：

```cmd
.venv\Scripts\activate.bat
```

macOS 或 Linux：

```bash
source .venv/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制环境变量模板：

```bash
cp .env.example .env
```

Windows PowerShell 可以使用：

```powershell
Copy-Item .env.example .env
```

然后在 `.env` 中填写模型和数据库配置。项目支持 OpenAI 兼容格式的大模型与 Embedding 服务。

```env
MODEL_PROVIDER=qwen
LLM_API_KEY=your_llm_api_key_here
LLM_BASE_URL=your_openai_compatible_chat_base_url_here
LLM_MODEL=your_chat_model_name_here

EMBEDDING_PROVIDER=qwen
EMBEDDING_API_KEY=your_embedding_api_key_here
EMBEDDING_BASE_URL=your_openai_compatible_embedding_base_url_here
EMBEDDING_MODEL=your_embedding_model_name_here

DATABASE_URL=sqlite:///./data/smart_appointment.db

DEBUG=True
LOG_LEVEL=INFO
```

常见配置方向：

- Qwen：使用阿里云百炼或 DashScope 的模型、Base URL 和 API Key。
- DeepSeek：可用于聊天模型，Embedding 可搭配其他兼容服务。
- Zhipu：可配置智谱的聊天模型和向量模型。
- Azure OpenAI：将 `MODEL_PROVIDER` 设置为 `azure`，并补充对应的 Azure OpenAI 环境变量。

### 4. 启动服务

```bash
python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

如果 8000 端口已被占用，可以换成 8001：

```bash
python -m uvicorn app:app --host 127.0.0.1 --port 8001 --reload
```

启动后可以访问：

- Web 页面：http://127.0.0.1:8000
- API 文档：http://127.0.0.1:8000/docs
- ReDoc 文档：http://127.0.0.1:8000/redoc

## 测试

运行全部测试：

```bash
pytest
```

运行单个测试文件：

```bash
pytest tests/test_task_classification_agent.py
```

当前测试基线请查看 `docs/BASELINE_REPORT.md`。本项目的部分测试会真实调用 LLM/OpenAI-compatible 接口，未配置可访问的模型服务时可能出现连接失败。

## 主要页面

当前阶段尚未修改前端模板文件，因此部分页面文件名或内部命名仍沿用原项目结构：

- 首页聊天与预约入口：`web/templates/index.html`
- 知识库管理：`web/templates/knowledge_management.html`
- 老师管理页面：`web/templates/technician.html`
- 老师可授课时间/排班页面：`web/templates/technician_schedule.html`
- 学习需求分析页面：`web/templates/user_behavior_analysis.html`

## 后续规划

### 更强的 Agent 自主能力

- 增加 Agent 自我反思机制，让系统能够评估课程咨询质量和排课成功率。
- 引入更完整的多轮推理链，提升复杂排课和冲突处理能力。
- 根据真实学生和家长反馈优化老师推荐策略。

### 更完整的多 Agent 协作

- 增加 Agent-to-Agent 通信机制，减少所有任务都依赖主分类器转发的问题。
- 将学习需求分析 Agent 的后台分析能力做得更稳定，支持定时任务和主动触达。
- 把预约、推荐、咨询之间的上下文记忆打通得更自然。

### 生产化能力

- 增加学生、家长、老师和课程顾问的权限控制和数据隔离。
- 增加更完整的异常处理和边界场景覆盖。
- 优化向量检索性能、缓存策略和响应速度。
- 支持 Docker 部署、云数据库和更标准的日志监控。

## 项目价值

这个项目把多 Agent、RAG、用户行为分析、预约调度和外部工具接入放在一个更贴近家教培训机构的真实业务场景中验证。它可以作为 AI Agent 工程化、分层架构、RAG 系统、自动化测试和业务自动化的综合实践项目。
