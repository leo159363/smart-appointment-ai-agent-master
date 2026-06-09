# CODEX Project Handoff

## 一、项目定位

- 项目名：基于多 Agent 与 RAG 的智能课程咨询系统
- 场景：AI 家教培训机构智能咨询与排课系统
- 背景：本项目从原通用预约/按摩场景迁移为家教机构场景，当前核心能力围绕课程咨询、老师匹配、试听课预约、正式排课、学习需求分析展开

## 二、已完成阶段

- 已完成领域迁移：按摩 / 技师 / 顾客 场景已迁移为 家教机构 / 老师 / 学生家长 / 试听课 / 排课
- 已完成本地 RAG：SQLite `knowledge_documents` + embedding + FAISS
- 已完成 Modular RAG MCP 接入：支持 `local / shadow / primary`
- 当前默认 `RAG_MCP_MODE=primary`
- Primary 模式优先调用 `MODULAR-RAG-MCP-SERVER` 的 `tutoring_course_kb`
- Modular 不可用时自动 fallback 到本地 FAISS
- 已验证 `primary_used_modular`
- 已验证 `final_source=modular_primary`
- 已验证 Modular 不可用时 `local_fallback`
- `/api/consultation/ask` 已修复：由错误的 `process_consultation()` 调整为 `consult()`
- GitHub Actions CI 已通过
- Fake LLM / Fake Embedding Provider 已完成，用于稳定 Agent 测试

## 三、当前关键配置

- 默认 RAG 配置：
  - `RAG_MCP_MODE=primary`
  - `RAG_MCP_TRANSPORT=mcp_stdio`
  - `RAG_MCP_COLLECTION=tutoring_course_kb`
- 测试环境配置：
  - `MODEL_PROVIDER=fake`
  - `EMBEDDING_PROVIDER=fake`
  - `RAG_MCP_MODE=local`

## 四、重要文件

- `config/rag_mcp_config.py`
- `services/rag_mcp_client.py`
- `agents/consultant/knowledge_retriever.py`
- `config/fake_llm_provider.py`
- `config/model_provider.py`
- `tests/conftest.py`
- `tests/test_task_classification_agent.py`
- `tests/test_appointment_agent.py`
- `tests/test_consultant_agent.py`
- `tests/test_user_behavior_agent.py`
- `api/consultation.py`
- `docs/` 下 RAG、架构、简历、面试相关文档

## 五、当前测试状态

- `import app` 通过
- `pytest --collect-only` 通过
- `pytest -q` 曾验证 `31 passed`
- Agent 测试已尽量避免真实 LLM key、真实网络和真实模型随机返回

## 六、禁止随便做的事

- 不要修改 `MODULAR-RAG-MCP-SERVER`
- 不要改 RAG Primary / fallback 默认逻辑
- 不要扩知识库
- 不要改数据库 schema
- 不要提交 `.env`
- 不要提交 `.venv/`
- 不要提交 `logs/`
- 不要提交 `data/*.db`
- 不要提交 `exports/`
- 不要提交 `.claude/`
- 不要提交 `CLAUDE.md`
- 不要提交 `__pycache__/`
- 不要提交 `.pytest_cache/`

## 七、下一步计划

- 如果 Fake LLM Provider 未 commit：先做受控提交、push、确认 CI
- 如果 Fake LLM Provider 已 commit 且 CI 绿：进入第 `10B-0` 学生画像记忆系统只读审计
- 第 `10B` 目标：设计学生画像记忆，字段包括：
  - 年级
  - 学科
  - 薄弱点
  - 学习目标
  - 可上课时间
  - 老师风格偏好
- 先只读审计，不直接写代码

## 八、给新窗口 Codex 的启动指令

### 新窗口启动提示词

请先读取 `docs/CODEX_PROJECT_HANDOFF.md`，恢复当前项目上下文，然后执行以下命令确认仓库状态：

```powershell
git status --short
git log --oneline -8
.\.venv\Scripts\python.exe -m pytest -q
```

根据当前状态判断下一步：

- 如果工作区不干净，先分类说明哪些文件是业务代码、测试文件、文档、生成物，再决定是否提交
- 如果 Fake LLM Provider 尚未提交或 CI 未确认，先做受控提交流程
- 如果 Fake LLM Provider 已提交且测试通过，进入 `第 10B-0：学生画像记忆系统只读审计`
- 在进入第 10B 之前，不要修改 `MODULAR-RAG-MCP-SERVER`，不要改 RAG Primary / fallback， 不要扩知识库，不要改数据库 schema
