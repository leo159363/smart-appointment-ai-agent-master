# 真实面试问题池 - AI 家教培训机构智能咨询与排课系统

本文是当前项目的本地面试题库。默认围绕家教/教培机构智能咨询与排课 MVP，不再使用旧本地服务预约场景作为项目主体。

## 收录原则

1. 问题必须服务于当前项目：课程咨询、老师匹配、试听课预约、正式排课、学习需求分析、RAG 课程知识库、测试基线和演示验收。
2. 可以询问领域迁移，但提问方式应是："如何将原预约系统迁移为家教培训机构智能咨询与排课系统？"
3. 对 `technician` 等内部兼容字段的提问应聚焦迁移风险控制，而不是要求立即重命名。
4. 每次模拟面试优先覆盖：项目介绍、多 Agent、RAG 存储/评估、测试基线、旧文案残留修复、已知问题表达。

## 真题列表

| ID | 问题 | 主题 | 类型 | 备注 |
|---|---|---|---|---|
| RQ01 | 请用 2-3 分钟介绍 AI 家教培训机构智能咨询与排课系统。 | 项目综述 | 开场题 | 必须讲清业务场景、架构和演示价值。 |
| RQ02 | 为什么把原预约系统迁移成家教培训机构场景？ | 领域迁移 | 真实性/动机 | 结合学生家教兼职背景和真实业务熟悉度。 |
| RQ03 | 这个项目有哪些核心模块？一次首页输入会经过哪些层？ | 架构 | 代码追问 | Web -> API/Router -> Task Agent -> Business Agent -> Service/DB/RAG。 |
| RQ04 | 多 Agent 是怎么分工的？为什么不做成一个大 Agent？ | Multi-Agent | 技术深挖 | 任务分类、咨询、预约/排课、学习需求分析。 |
| RQ05 | 任务分类 Agent 失败时为什么会影响测试？你怎么分类这个失败？ | 测试基线 | 测试开发 | A 类外部 LLM/OpenAI-compatible 连接失败。 |
| RQ06 | 预约/排课 Agent 如何处理缺失信息？为什么不能暴露 duration/gender？ | 用户体验 | 代码追问 | 业务字段映射、自然追问、内部字段兼容。 |
| RQ07 | 老师匹配现在怎么做？Embedding 在哪里参与？ | 老师匹配 | 代码追问 | `TechnicianFinder`, `services/text_embedding.py`, teacher strength similarity。 |
| RQ08 | 当前 RAG 课程知识库如何存储和检索？ | RAG 存储 | 技术深挖 | SQLite 文档 + embedding + FAISS index。 |
| RQ09 | RAG 检索质量你会怎么评估？ | RAG 评估 | 测试开发 | Hit@K, MRR, context precision, answer faithfulness, business checklist。 |
| RQ10 | 当前 RAG 架构是怎样的？Modular RAG 和本地 FAISS 如何配合？ | 跨项目对比 | 架构边界 | 默认 `primary` 模式优先走 Modular RAG MCP；本地 FAISS 保留为 fallback；可切 `local` 完全走本地。 |
| RQ11 | `reset_demo_data.py` 解决了什么问题？为什么不强制提交 SQLite DB？ | 演示数据 | 工程化 | 可重建演示数据，避免本地 DB/备份污染仓库。 |
| RQ12 | 你如何发现并修复旧场景文案残留？ | 缺陷定位 | 测试开发 | 关键词扫描、页面/API/DB 数据源定位、D 类问题。 |
| RQ13 | `[object Object]`、`default_user`、`duration/gender` 分别是什么类型的问题？ | 前端/体验 | 缺陷分类 | 渲染对象、内部 ID 泄露、内部字段泄露。 |
| RQ14 | FastAPI 的启动流程和页面/API 文档入口是什么？ | 后端 | 基础题 | `app.py`, routers, startup init, `/docs`。 |
| RQ15 | 如何向面试官解释全量 pytest 不是全绿？ | 质量表达 | 风险表达 | 已知基线、A/B/C 分类、后续 fake/mock LLM。 |
| RQ16 | 后续如果做测试开发项目包装，你会补哪些测试？ | 测试设计 | 开放题 | API 自动化、Playwright、RAG eval、mock LLM、CI。 |

## 主题映射

| 主题 | 题号 | 重点 |
|---|---|---|
| 项目定位 | RQ01, RQ02 | 家教培训机构、领域迁移、MVP 边界。 |
| 架构与后端 | RQ03, RQ14 | FastAPI, API, Agent, Service, SQLite, FAISS。 |
| Multi-Agent | RQ04, RQ05, RQ06 | 路由、状态、缺失信息、fallback。 |
| RAG | RQ08, RQ09, RQ10 | SQLite/FAISS/Embedding、评估、MCP 扩展边界。 |
| 测试开发 | RQ05, RQ11, RQ12, RQ13, RQ15, RQ16 | 基线、缺陷分类、回归、演示验收。 |
