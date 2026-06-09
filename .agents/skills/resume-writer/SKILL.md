---
name: resume-writer
description: "基于 AI 家教培训机构智能咨询与排课系统生成定制化简历项目经历。围绕测试开发、Agent 应用、RAG 课程知识库、FastAPI 后端、自动化测试与质量保障进行中文或英文项目包装。Use when user says '写简历', '简历项目', '项目经历', 'resume', 'write resume', '包装项目', '优化简历', '家教项目简历', '教培 Agent 简历', '测试开发项目简历', or asks to generate resume content based on this tutoring project."
---

# Resume Writer

基于"真实业务场景 + 技术亮点 + 质量保障 + 包装边界"生成当前项目的简历描述。默认中文输出，用户要求时提供英文版。

## Phase 1: Load Knowledge

Before writing, read:

1. `references/resume_principles.md` for structure and anti-patterns.
2. `references/project_highlights.md` for technical highlights and source anchors.
3. `references/packaging_reference.md` for allowed packaging strength and boundaries.
4. `README.md`, `docs/BASELINE_REPORT.md`, and relevant source files when exact implementation detail is needed.

If the user asks about `MODULAR-RAG-MCP-SERVER-main`, it is already integrated as the default primary retrieval source. Do not claim it replaces local FAISS entirely — fallback remains.

## Phase 2: Collect User Intent

Ask up to 4 questions:

1. Target role: 测试开发 / Agent 应用 / RAG 工程 / FastAPI 后端 / 全栈 AI / 通用软件开发.
2. Output style: 简历 bullets / 项目介绍 / STAR / 面试话术 / 英文版.
3. Emphasis: 测试基线 / 多 Agent / RAG 知识库 / 预约排课流程 / 学习需求分析 / 页面 API 验收.
4. Constraints: 篇幅、是否要量化指标、是否突出迁移过程、是否提及未来 RAG/MCP 扩展.

If the user wants a quick version, assume target role is **测试开发实习** and emphasize baseline, regression, defect classification, and manual/API validation.

## Phase 3: Recommended Project Names

Default project name:

- 基于多 Agent 与 RAG 的智能课程咨询系统

Other acceptable names:

- AI 家教培训机构智能咨询与排课系统
- AI 驱动的教育咨询与排课自动化平台
- 面向教培机构的 Agent + RAG 质量保障项目

For test-development resumes, prefer:

**基于多 Agent 与 RAG 的智能课程咨询系统**

## Phase 4: Content Generation

Use the four-part structure:

1. Background: tutoring/training institution consultation, teacher matching, trial lessons, formal scheduling, and learning follow-up.
2. Goal: build a runnable MVP with Multi-Agent routing, RAG course knowledge, SQLite demo data, and quality baseline.
3. Process: 4-6 bullets, each with action, implementation detail, and evidence.
4. Result: measurable or verifiable outputs, clearly marked if suggested.

## Role-Based Emphasis

| Role | Priority |
|---|---|
| 测试开发 | baseline, pytest collect, page/API validation, old-text scan, A/B/C/D/E risk classification, reset demo data |
| Agent 应用 | task routing, appointment/scheduling state, consultation Agent, learning-need Agent, fallback design |
| RAG 工程 | KnowledgeService, SQLite documents, FAISS, embeddings, Modular RAG MCP primary retrieval + fallback, retrieval quality, RAG/MCP expansion roadmap |
| FastAPI 后端 | app startup, routers, API layer, services, DB router, streaming response |
| 全栈 AI | Web pages, `/chat/stream`, API docs, demo data, end-to-end flow |

## Bullet Requirements

Each bullet should:

- Start with a strong verb: 设计、实现、构建、优化、建立、验证、定位、沉淀.
- Include a source-code or test anchor when useful.
- Avoid claiming production deployment or fully completed internal rename.
- Mention current MVP boundary honestly: some internal fields are retained for compatibility.

Example bullet themes:

- 建立迁移测试基线：`import app`、`pytest --collect-only`、targeted pytest、manual validation.
- 设计多 Agent 任务分发：classification -> consultation/appointment/user behavior.
- 构建 RAG 课程知识库：SQLite + FAISS + embedding, course rules and pricing.
- 修复演示体验 defects：old text residue, `[object Object]`, `default_user`, internal field leakage.
- 沉淀 demo reset: `scripts/reset_demo_data.py` rebuilds tutoring demo data without schema change.

## Quantification Guidance

Use real numbers when available. If suggested numbers are used, mark them as "建议值，需按实际验证调整".

Available verified facts:

- pytest collect-only can collect 30 tests.
- targeted task classification test currently has 1 known failure due to LLM/OpenAI-compatible connection.
- `import app` smoke test passes.
- pages and APIs were manually validated during the migration stages.
- SQLite demo data can be rebuilt through `scripts/reset_demo_data.py`.

Suggested metrics:

| Metric | Suggested Range | Notes |
|---|---:|---|
| Intent routing scenario coverage | 20+ cases | Use only after building cases. |
| RAG Hit@3 | 80%-90% | Requires future eval set. |
| Page smoke validation | 6 pages | Homepage, docs, knowledge, teacher, schedule, learning analysis. |
| API smoke validation | 5+ APIs | Knowledge, teachers, appointment, consultation, user behavior. |
| Regression categories | 5 classes | A/B/C/D/E risk taxonomy. |

## Output Template

```markdown
**[项目名称]** | [时间段] | [角色]

**背景**：[2-3 句描述家教/教培机构课程咨询、老师匹配、试听课预约和正式排课痛点]

**目标**：[1-2 句说明 Multi-Agent + RAG + 测试基线 + 可运行 MVP 目标]

**过程**：
• [Bullet 1：测试基线/迁移质量保障]
• [Bullet 2：Multi-Agent 任务分发]
• [Bullet 3：RAG 课程知识库]
• [Bullet 4：试听课预约/正式排课流程]
• [Bullet 5：学习需求分析/演示数据重置/页面 API 验收]

**结果**：[2-3 句汇总可验证结果；建议指标需标注]

**技术栈**：[FastAPI, LangChain, FAISS, SQLite, SQLAlchemy, pytest, Jinja2, Multi-Agent, RAG]
```

## Packaging Boundaries

Allowed:

- Say the project is a tutoring-domain MVP migrated and validated in stages.
- Say the RAG architecture has two layers: Modular RAG MCP as the default primary retrieval source, with local SQLite + FAISS as fallback.
- Say both layers serve the Knowledge-Document-Retrieval-Generation pipeline and Modular is already integrated (not future work).
- Say internal compatibility fields such as `technician` remain to reduce migration risk.

Forbidden:

- Do not claim full production deployment.
- Do not claim the internal naming refactor is complete.
- Do not claim all tests are green.
- Do not claim the Modular RAG MCP Server is a future plan — it is already integrated as the default primary retrieval source with local FAISS fallback.
- Do not invent real users, revenue, traffic, or business contracts.

## Interview Follow-Up Predictions

After writing, provide 3-5 likely questions:

- 为什么老师相关内部字段还叫 `technician`？
- 当前 RAG 是怎么存储、检索和评估的？
- 任务分类测试失败为什么不立即修？
- 你怎么定位页面旧文案和 `[object Object]` 问题？
- 如果继续做测试开发项目，你会补哪些自动化测试？
