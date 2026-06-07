# CI/CD 说明

## 1. 当前阶段

当前项目只接入 CI，不做 CD。CI 用于在 push 或 pull request 后自动执行基础质量检查，帮助确认项目入口、测试收集和辅助脚本仍然可用。

CD 自动部署属于后续优化，本阶段不会自动发布、自动部署，也不会自动生成 commit。

## 2. CI 检查内容

当前 GitHub Actions 工作流执行以下检查：

- 安装 `requirements.txt` 中的依赖。
- 执行 `import app` smoke test。
- 执行 `pytest --collect-only`，确认测试可收集。
- 对 RAG 导出脚本执行 `py_compile` 语法检查。
- 执行 RAG 导出脚本 `--help`，确认 CLI 可用。

CI 不读取 `.env`，不要求真实 LLM 或 embedding API key，也不打印任何密钥。

为保证 `import app` 和 `pytest --collect-only` 能在无 `.env` 的 GitHub Actions 环境中完成模块加载，CI 会配置一组 dummy LLM/embedding 环境变量。这些值只用于 SDK 初始化，不是真实密钥，也不会用于真实模型请求。

GitHub Actions checkout 不会自动包含本地空目录，因此 CI 会在运行时创建 `data/` 和 `exports/` 目录，避免 SQLite 默认路径 `data/smart_appointment.db` 因目录不存在导致 `import app` 失败。CI 不提交 SQLite 数据库文件，`data/smart_appointment.db` 仍属于本地演示数据，可通过 `scripts/reset_demo_data.py` 在本地生成。当前 CI 只做基础质量检查，不强依赖本地演示数据库内容。

## 3. 为什么不把 task_classification 作为阻塞项

当前 `task_classification` 相关测试存在已知 A 类问题，主要受 LLM/OpenAI-compatible 连接失败影响。该类失败属于外部依赖问题，不适合作为当前最小 CI 的阻塞项。

后续计划引入 fake/mock LLM provider 后，再把 Agent 单测和更多业务回归测试纳入阻塞 CI。

在 fake/mock provider 完成前，CI 不执行真实 LLM 调用，也不把依赖真实 LLM/OpenAI-compatible 服务的 Agent 单测作为阻塞检查。

## 4. 为什么不做 CD

当前项目是本地 MVP 演示系统，尚未准备完整的 Docker 镜像、云服务器环境、数据库迁移策略和 GitHub Secrets 密钥管理。

在这些部署基础设施完成前，直接做 CD 容易把本地演示环境、模型配置和数据库状态混在一起，增加不可控风险。因此当前阶段只做 CI，不做自动部署。

## 5. 后续优化

后续可以逐步增加：

- mock/fake LLM provider。
- API 自动化测试。
- Playwright 页面验收。
- RAG golden set 自动评估。
- Docker build 检查。
- GitHub Secrets 管理。
- 部署到云服务器、Render、Railway 等环境。
