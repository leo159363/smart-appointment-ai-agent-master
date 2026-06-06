# 项目知识锚点 - AI 家教培训机构智能咨询与排课系统

## 总体架构

- `app.py`: FastAPI 应用创建、路由注册、系统启动初始化。
- `web/templates/`: 首页、课程知识库、老师状态、老师课表、学习需求分析页面。
- `web/routes.py`: 页面路由和 `/chat/stream` 流式聊天入口。
- `api/`: REST API 层，包含课程咨询、任务分类、预约/排课、老师、知识库、学习需求分析。
- `agents/`: 多 Agent 编排层。
- `services/`: 知识库、老师、预约、学习需求等服务层。
- `db/`: SQLite 模型、Repository、Router。
- `scripts/reset_demo_data.py`: 备份并重置本地演示数据，不修改 schema。
- `tests/`: pytest 自动化测试基线。

## 多 Agent 编排

- `agents/task_classification_agent.py`: 总入口，初始化任务分类、预约、咨询 Agent。
- `agents/task_classification/task_classifier.py`: 将输入归类为 appointment/query/pay/statistics/other。
- `agents/task_classification/agent_router.py`: 根据分类结果路由到预约/排课 Agent 或咨询 Agent。
- `agents/appointment_agent.py`: 试听课预约/正式排课主控制器，维护会话状态。
- `agents/consultant_agent.py`: 课程咨询/RAG 问答入口。
- `agents/user_behavior_agent.py`: 学习需求分析、回访提醒、偏好分析。

面试要点:

- 多 Agent 拆分减少单 Agent 上下文膨胀和职责混乱。
- 当前是中心化编排，不要夸大成复杂 P2P Agent 网络。
- `technician`、`appointment`、`service_type`、`technician_id` 是 MVP 阶段保留的历史兼容字段，对外语义已经迁移为老师、课程、试听课和排课。

## 预约/排课流程

- `agents/appointment/input_parser.py`: 将自然语言抽取到内部兼容字段。
- `agents/appointment/appointment_processor.py`: 更新预约状态、判断缺失信息、处理推荐确认、生成成功/失败回复。
- `agents/appointment/message_builder.py`: 构建用户可见消息，包含内部字段到中文业务字段的映射。
- `agents/appointment/technician_finder.py`: 老师匹配，可按性别、偏好、相似教学方向查找可授课老师。
- `agents/appointment/appointment_database.py`: 保存预约/课表数据。

面试要点:

- 老师性别偏好不是必填项，缺失时应匹配任意合适老师。
- 不能向用户暴露 `duration/gender` 这类内部字段。
- `[请确认具体时间]` 这类占位值不能进入成功流程，应继续追问具体日期和时间。

## RAG 与课程知识库

- `services/knowledge_service.py`: 默认课程知识库、embedding、FAISS index、SQLite 文档管理。
- `agents/consultant/knowledge_retriever.py`: 检索课程知识。
- `agents/consultant/prompt_builder.py`: 构建课程咨询 prompt。
- `agents/consultant/response_generator.py`: 生成回答，并对收费/课时包问题提供规则型兜底。

面试要点:

- 当前 RAG 是轻量内置方案：SQLite documents + Embedding + FAISS。
- 知识覆盖课程体系、收费规则、老师介绍、试听/排课规则、课时包/课程包、教学质量等。
- RAG 评估可以覆盖 Hit@K、MRR、context precision、faithfulness、业务关键点覆盖率。
- `MODULAR-RAG-MCP-SERVER-main` 可作为后续独立 RAG/MCP 知识层和评估层，不要声称当前已完整合并。

## 学习需求分析

- `agents/user_behavior_agent.py`: 行为记录、偏好分析、回访提醒。
- `agents/user_behavior/pattern_analyzer.py`: 分析偏好老师、常选课程/学科、时长、回访时机。
- `web/templates/user_behavior_analysis.html`: 展示学习需求、回访消息和建议试听/排课时间。
- `api/user_behavior_analysis.py`: 学习需求分析 API。

面试要点:

- `[object Object]` 是前端对象数组未格式化问题。
- `default_user` 是内部默认 user_id，不应直接展示给用户。
- 学习需求分析适合包装为测试开发中的真实 UI/API 验收案例。

## 测试基线与缺陷分类

基线命令:

```powershell
.\.venv\Scripts\python.exe -c "import app; print('app import ok')"
.\.venv\Scripts\python.exe -m pytest --collect-only
.\.venv\Scripts\python.exe -m pytest tests/test_task_classification_agent.py -q
```

风险分类:

- A 类: LLM/OpenAI-compatible 连接失败。
- B 类: 测试与当前实现不一致。
- C 类: SQLite 数据写入或数据处理问题。
- D 类: 页面/API/演示数据旧文案残留。
- E 类: 真实功能阻塞问题。

面试要点:

- 当前任务分类单测仍可能因外部 LLM 连接失败而失败，这是已知 A 类问题。
- 测试开发价值在于先建立基线、分阶段修改、每阶段验证、记录失败原因，而不是为全绿盲目改业务逻辑。
