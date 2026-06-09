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

- 第 `10B-0` 到 `10B-1E` 已完成：学生画像服务、咨询 API、首页 `/chat` 咨询链路和预约/排课辅助提示均已接入。
- 第 `10B-2` 当前目标：完成学生画像记忆系统整体验收与文档同步。
- 本轮文档同步后不要自动 commit；等待用户确认后再做受控 docs 提交。
- 继续保持边界：不修改 `MODULAR-RAG-MCP-SERVER`，不改 RAG Primary / fallback，不扩知识库，不改数据库 schema，不改 `/chat/stream`。

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
- 如果工作区只有文档变更，等待用户确认后再做受控 docs 提交
- 学生画像记忆系统已经接入咨询和预约链路，后续只在用户明确要求时继续扩展
- 不要修改 `MODULAR-RAG-MCP-SERVER`，不要改 RAG Primary / fallback，不要扩知识库，不要改数据库 schema，不要改 `/chat/stream`

## 九、10B 学生画像记忆系统当前状态

第 `10B-0` 到 `10B-1E` 已完成学生画像记忆系统最小闭环：

- `services/student_profile_service.py` 复用 `user_behaviors` 表保存画像更新事件，不新增表，不改数据库 schema
- 画像事件使用 `action_type="student_profile_update"`，`action_data` 保存画像字段 JSON
- 最小画像字段包括 `grade`、`subject`、`weak_points`、`learning_goal`、`available_time`、`teacher_style_preference`
- `/api/consultation/ask` 支持 `user_id`，会从 `question` 中规则提取画像、写入更新事件、读取最新画像并交给 `ConsultantAgent`
- 首页 `/chat` 支持 `user_id`，咨询类消息会读取和更新画像；`/chat/stream` 保持原调用方式
- `ConsultantAgent` 将画像格式化为补充 prompt 上下文，且不替代 RAG 检索结果
- `AppointmentAgent` 读取画像中的学科、可上课时间和老师风格偏好，只用于缺失信息提示
- 画像不会自动替用户确认预约，不会自动下单，不会覆盖用户本轮明确输入
- 没有画像时保持原咨询/预约流程；没有 `user_id` 时兼容 `default_user`

当前关键验证：

```powershell
.\.venv\Scripts\python.exe -c "import app; print('app import ok')"
.\.venv\Scripts\python.exe -m pytest --collect-only
.\.venv\Scripts\python.exe -m pytest -q
```

当前测试基线已验证 `52 passed`。继续保持边界：不修改 `MODULAR-RAG-MCP-SERVER`，不改 RAG Primary / fallback，不扩知识库，不改数据库 schema，不改 `/chat/stream`。本轮文档同步后等待用户确认，再做受控 docs 提交。
