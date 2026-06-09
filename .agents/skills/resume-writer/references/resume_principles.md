# 简历编写原则

## 1. 四段式结构

- **背景**：面向家教/教培机构的课程咨询、老师匹配、试听课预约、正式排课和学习跟进。
- **目标**：基于 FastAPI、多 Agent、RAG 课程知识库和 SQLite 演示数据构建可运行 MVP，并建立测试/验收基线。
- **过程**：说明做了什么、用什么技术、如何验证。
- **结果**：用可验证事实或明确标注的建议指标说明成果。

## 2. 技术标签维度

| 方向 | 关键词 |
|---|---|
| Agent 架构 | Multi-Agent, Task Routing, Agent Orchestration, State Manager, Fallback |
| RAG 检索 | RAG, FAISS, Embedding, Vector Search, Knowledge Base, Retrieval Quality |
| 后端工程 | FastAPI, AsyncGenerator, SQLAlchemy, SQLite, Repository Pattern, Layered Architecture |
| 测试评估 | pytest, Smoke Test, Regression Test, Scenario Test, API Validation, UI Validation |
| 质量保障 | Baseline, Defect Classification, Keyword Scan, Demo Data Reset, Known Issues |

## 3. 差异化策略

1. 强调真实业务迁移：从原始预约项目迁移到更熟悉的家教培训场景。
2. 强调测试开发能力：先基线、后迁移、每阶段验证、分类记录失败。
3. 强调可运行 MVP：页面、API、SQLite 演示数据均可手工验收。
4. 强调边界清晰：内部兼容字段保留，后续再做重构。

## 4. 常见误区

| 误区 | 修正 |
|---|---|
| 只堆工具 | 说明每个工具解决什么质量或业务问题。 |
| 说测试全绿 | 当前仍有 LLM 连接相关已知失败，应如实表达。 |
| 过度包装 RAG/MCP | 当前已接入 Modular RAG MCP 作为默认 primary 检索层，但本地 FAISS 仍为 fallback，不应说成已完全替换。 |
| 避谈迁移边界 | 主动解释保留内部字段是风险控制。 |

## 5. 输出质量要求

- 每条 bullet 不超过 90 字。
- 优先使用动词开头。
- 至少包含一个测试或验收相关 bullet。
- 量化指标必须可解释，建议值必须标注。
