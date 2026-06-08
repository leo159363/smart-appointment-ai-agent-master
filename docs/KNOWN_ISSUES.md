# 已知问题与后续优化

## 1. 当前 MVP 边界

当前系统是可运行 MVP，重点是完成家教培训机构场景迁移、Agent/RAG 链路、页面/API 验收、SQLite 演示数据和 CI 基础检查。它还不是完整生产系统。

当前阶段优先保证：

- 首页咨询、试听课预约、老师匹配、知识库和学习需求分析可演示。
- 迁移后的业务语义对外一致。
- 演示数据可重建。
- 基础 CI 能跑绿。
- 已知问题有清晰分类和后续计划。

## 2. 已知问题

1. LLM/OpenAI-compatible 外部连接失败会影响部分 Agent 单测。
2. 内部仍保留 `technician`、`appointment`、`service_type`、`technician_id` 等历史兼容字段。
3. `data/smart_appointment.db` 不强制提交，演示数据通过 `scripts/reset_demo_data.py` 重建。
4. MODULAR-RAG-MCP-SERVER 已完成 Eval-only、Shadow 和 Primary 主检索层联调，当前默认是 primary，并保留本地 FAISS fallback；更大规模知识库、量化评估和完整 LLM 端到端稳定测试仍待完善。
5. 当前没有登录鉴权和 RBAC 权限隔离。
6. 当前没有 Playwright 页面自动化。
7. 当前没有 Docker/CD 部署。
8. 全量 pytest 中仍有历史基线失败，需要后续分类修复。

## 3. 为什么这些问题当前可接受

LLM/OpenAI-compatible 失败属于外部依赖问题。当前 CI 已避免真实 LLM 调用，后续通过 fake/mock LLM provider 可以让 Agent 测试稳定进入阻塞 CI。

内部字段保留是为了降低数据库、路由、前端调用和测试基线同时重构的风险。当前优先保证对外语义正确，内部命名后续可以按模块渐进重构。

SQLite 本地演示数据不提交，是为了避免把运行文件、备份文件和本地状态带入仓库。演示数据通过 `scripts/reset_demo_data.py` 可重建，更适合面试和本地演示。

MODULAR-RAG-MCP-SERVER 采用 local、Shadow、Primary 分阶段策略，是为了先建立检索评估指标，再逐步扩大影响面。即使启用 Primary，也保留本地 FAISS fallback，避免 Modular 服务不可用时影响咨询回答。

当前已完成的 Modular RAG 范围包括 Eval-only 数据导出、Shadow 对比日志、Primary 主检索层真实联调和本地 FAISS fallback。仍待完善的是更大规模课程知识库、RAG 量化评估、完整 LLM 端到端稳定测试、Modular 服务部署化，以及 CI 中不真实调用 Modular 的自动化验证边界。

登录鉴权、RBAC、Docker 和 CD 属于生产化增强。当前项目目标是展示 AI 应用、RAG、测试基线和工程化交付能力，不把生产部署能力提前混入 MVP。

Playwright 页面自动化尚未接入，是因为当前优先完成场景迁移、手工验收和 CI 基础检查。后续页面稳定后再接入自动化更合适。

全量 pytest 的历史失败需要按 A/B/C/D/E 分类修复，不能为了全绿盲目改业务逻辑。当前基础质量门禁是应用可导入、测试可收集、CI 可通过。

## 4. 后续优化路线

### P0

- 引入 fake/mock LLM provider。
- 稳定 Agent 单测。
- 补充 API 自动化测试。

### P1

- 接入 Playwright 页面自动化。
- 接入 RAG golden set 自动评估。
- 持续分析 MODULAR-RAG-MCP-SERVER 的 Shadow/Primary 日志，对比本地 RAG 和独立 RAG/MCP 检索结果。
- 扩展 `tutoring_course_kb` 知识规模，并统计 hit@k、MRR、latency 和 fallback 原因。

### P2

- 渐进重构内部兼容字段。
- 增加登录鉴权和 RBAC 权限隔离。
- Docker 化本地运行环境。
- 部署化 Modular RAG 服务。
- 设计 CD 部署流程。
- 在 CI 中加入 Docker build 和更多稳定测试。
