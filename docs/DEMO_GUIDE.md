# 演示指南

## 1. 演示前准备

建议在演示前重置本地 SQLite 演示数据，确保课程知识、老师数据、课表和用户行为分析结果处于可讲解状态。

```powershell
.\.venv\Scripts\python.exe scripts/reset_demo_data.py
```

## 2. 启动服务

```powershell
.\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
```

启动后保持终端运行，浏览器访问本地页面。

## 3. 页面入口

- 首页：`http://127.0.0.1:8000/`
- API 文档：`http://127.0.0.1:8000/docs`
- 知识库管理：`http://127.0.0.1:8000/knowledge`
- 老师状态：`http://127.0.0.1:8000/technician`
- 老师课表：`http://127.0.0.1:8000/technician_schedule`
- 学习需求分析：`http://127.0.0.1:8000/user_behavior_analysis`

说明：老师相关页面路径中仍保留 `technician`，这是从通用预约系统迁移到家教培训机构场景时为兼容旧接口保留的内部命名。

## 4. 推荐演示顺序

1. 打开首页，说明这是 AI 家教培训机构智能咨询与排课系统。
2. 在聊天框输入课程咨询问题，展示任务识别和咨询回答。
3. 进入知识库管理页面，展示课程知识条目和本地 RAG 知识来源。
4. 进入老师状态页面，展示老师信息、学科和可用状态。
5. 进入老师课表页面，展示排课数据。
6. 进入学习需求分析页面，展示学生/家长行为分析、偏好老师和跟进建议。
7. 打开 `/docs`，展示 FastAPI 自动生成的 API 文档。
8. 说明 GitHub Actions CI 已跑绿，当前 CI 覆盖应用导入、测试收集和 RAG 导出脚本检查。

## 5. 推荐演示问题

可以在首页聊天入口输入：

- 初二数学基础比较差，想先约一节试听课。
- 高一物理力学听不懂，有没有适合冲刺提分的老师？
- 周六下午可以安排英语试听课吗？
- 试听课、10课时包和20课时包有什么区别？
- 线上课和线下课都支持吗？
- 想找一位耐心一点的老师，孩子基础比较弱。

演示时可重点说明系统会围绕年级、科目、学习基础、目标、时间偏好和联系方式逐步收集信息，并把课程咨询、预约排课和老师匹配区分处理。

## 6. 测试与 CI 演示

本地可执行以下基础检查：

```powershell
.\.venv\Scripts\python.exe -c "import app; print('app import ok')"
```

```powershell
.\.venv\Scripts\python.exe -m pytest --collect-only
```

```powershell
.\.venv\Scripts\python.exe -m py_compile scripts/export_tutoring_kb_for_modular_rag.py
```

```powershell
.\.venv\Scripts\python.exe scripts/export_tutoring_kb_for_modular_rag.py --help
```

GitHub Actions 中的 `CI / Basic quality checks` 已配置同类基础检查，并在最新提交上跑绿。当前 CI 不执行真实 LLM 调用，不依赖真实 API key，也不做自动部署。

## 7. 面试讲解重点

- 迁移不是只改名称，而是把通用预约系统迁移到家教培训机构业务域。
- 系统使用 FastAPI + 多 Agent + 本地 RAG + SQLite 演示数据完成 MVP 闭环。
- 当前保留部分 `technician` 内部命名，是为了降低迁移风险和保持旧接口兼容。
- CI 已覆盖基础质量检查，后续可以继续加入 mock LLM、API 自动化测试、Playwright 页面验收和 RAG golden set 自动评估。
- MODULAR-RAG-MCP-SERVER 已支持 Shadow 对比和 Primary 主检索模式；当前默认是 primary，优先调用 Modular RAG，本地 FAISS 保留为 fallback。
