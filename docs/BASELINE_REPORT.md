# 基线验证报告

记录日期：2026-06-03

本报告只记录当前 `smart-appointment-ai-agent-master` 的环境和运行基线。本阶段不修改核心业务代码、不读取或打印 `.env`、不修改数据库模型、不修改 API 路由、不修改 Agent prompt、不修改前端页面。

## 1. 当前启动命令

推荐使用项目内虚拟环境启动：

```powershell
.\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
```

如果需要热重载，可在本地开发时使用：

```powershell
.\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

当前 API 文档预期地址：

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/redoc`

## 2. 当前测试命令

当前统一使用 `.venv` 运行 pytest：

```powershell
.\.venv\Scripts\python.exe -m pytest --collect-only
.\.venv\Scripts\python.exe -m pytest tests/test_task_classification_agent.py -q
.\.venv\Scripts\python.exe -m pytest -q
```

## 3. 当前 Python 和依赖状态

| 检查项 | 当前结果 |
| --- | --- |
| Python 版本 | `Python 3.11.7` |
| `.venv` Python | `Python 3.11.7` |
| `.venv` FastAPI | `fastapi 0.115.14` |
| `.venv` Uvicorn | `uvicorn 0.48.0` |
| `.venv` LangChain Core | `langchain-core 0.3.86` |
| `.venv` pytest | `pytest 9.0.3` |
| `.venv` pytest-asyncio | `pytest-asyncio 1.4.0` |

当前判断：

- `.venv` 已具备启动 FastAPI 和运行 pytest 的主要依赖。
- pytest 已能从项目根目录识别 `agents` 包。
- 后续建议继续统一使用 `.venv` 运行启动和测试，避免全局 Python 与虚拟环境混用。

## 4. 当前测试状态

pytest 收集状态：

- 命令：`.\.venv\Scripts\python.exe -m pytest --collect-only`
- 结果：成功
- 总测试数：`30`
- 收集是否成功：成功
- `agents` 导入问题：已经解决
- 当前失败阶段：测试执行阶段，不再是 pytest 收集阶段

单个任务分类测试状态：

- 命令：`.\.venv\Scripts\python.exe -m pytest tests/test_task_classification_agent.py -q`
- 结果：`1 failed, 7 passed`
- 报错摘要：任务分类调用 LLM/OpenAI-compatible 接口时出现连接失败，随后返回兜底文案 `暂不支持该类型任务...`
- 判断：已进入测试执行阶段，失败不再是导入路径问题。

全量测试状态：

- 命令：`.\.venv\Scripts\python.exe -m pytest -q`
- 结果：`16 failed, 14 passed`
- 总测试数：`30`
- 通过数：`14`
- 失败数：`16`
- 收集是否成功：成功

## 5. FastAPI 是否能启动

当前可确认状态：

- `.venv\Scripts\python.exe -m uvicorn --version` 可运行。
- `.venv\Scripts\python.exe -c "import app; print('app import ok')"` 可运行，输出 `app import ok`。
- 当前 `127.0.0.1:8000` 没有监听服务。
- 当前项目目录存在 `data/smart_appointment.db`，说明本地 SQLite 数据文件已经生成。

已知约束：

- 应用导入和启动会加载模型配置。
- 完整 startup 会初始化知识库，并可能调用 embedding 模型。
- 如果模型或 embedding 环境变量缺失、无效或无法访问外部服务，完整启动可能失败。
- 本阶段没有读取或打印 `.env`，因此不确认本地模型凭据是否完整。

当前结论：

- 项目具备使用 `.venv` 加载 FastAPI 应用入口的基础条件。
- 当前服务没有运行。
- 完整启动是否成功取决于模型/embedding 环境变量和网络可用性。

## 6. 剩余失败分类

| 分类 | 失败类型 | 报错/现象 | 本阶段建议 |
| --- | --- | --- | --- |
| A 类 | 外部依赖失败 | LLM/OpenAI-compatible 接口连接失败，典型报错为 `openai.APIConnectionError: Connection error`。 | 第 2 阶段暂不修复；后续优先采用 mock/fake LLM 或测试专用 provider。 |
| B 类 | 测试与当前实现不一致 | 测试期望 `insight_provider`、`behavior_processor`、`recommendation_engine`、`recommendation_generator`、`save_preferences` 等属性或方法，但当前实现不存在。 | 第 2 阶段暂不修复；后续先审计当前真实 API，再决定补实现或调整测试。 |
| C 类 | 真实业务/数据处理问题 | 有些行为数据把 `dict` 直接写入 SQLite 字段，触发 `sqlite3.ProgrammingError`。 | 第 2 阶段暂不修复；后续最小修复方向是入库前序列化或调整数据访问层。 |

## 7. 当前存在的报错

| 来源 | 报错摘要 | 判断 |
| --- | --- | --- |
| 任务分类测试 | LLM/OpenAI-compatible 接口连接失败，返回兜底文案 | A 类外部依赖失败。 |
| 全量 Agent 测试 | 多个测试真实调用 LLM，出现 `Connection error` | A 类外部依赖失败。 |
| 用户行为测试 | 当前实现缺少测试期望的若干属性或方法 | B 类测试与实现不一致。 |
| 用户行为入库 | `dict` 直接写入 SQLite 字段，触发 `sqlite3.ProgrammingError` | C 类真实业务/数据处理问题。 |
| 完整 FastAPI startup | 可能缺模型或 embedding 凭据 | 需要本地环境变量配置；本阶段不读取 `.env`。 |

## 8. 当前阶段结论

- `agents` 导入路径问题已经解决。
- pytest 已可收集并执行测试。
- 当前测试总数为 `30`，执行结果为 `14 passed, 16 failed`。
- 剩余失败暂不在第 2 阶段修复。
- 第 2 阶段可以继续进行对外文案和默认数据迁移。
- 后续如果修复测试，应优先采用 mock/fake LLM 或测试专用 provider，而不是依赖真实外部接口。

## 9. 当前不建议立即修复的问题

- 不建议当前阶段改 Agent prompt。
- 不建议当前阶段改数据库模型。
- 不建议当前阶段改 API 路由。
- 不建议当前阶段改前端页面。
- 不建议通过硬编码绕过 LLM、OpenAI-compatible 接口或 embedding。
- 不建议为了测试通过而删除测试。
- 不建议现在重命名 `technician`、数据库表、Repository 或路由路径。
- 不建议现在整合 `MODULAR-RAG-MCP-SERVER-main`。
