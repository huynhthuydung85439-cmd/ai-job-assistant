# CloudBase 求职展示预览版配置

## 部署范围

CloudBase 第一版用于求职展示预览。关系数据继续使用 CloudBase MySQL，注册登录、
简历解析、JD 匹配、普通 AI 对话和历史记录保持可用。

仓库根目录的 `Dockerfile` 是 CloudBase 轻量后端镜像，仅运行 FastAPI API、数据库迁移和
健康检查，不构建或包含 `frontend/`。CloudBase 后端与前端静态站点是两项独立部署；前端
使用的具体托管产品、域名和平台配置需在实际部署平台确认。

### 前端独立构建

前端通过以下流程单独构建：

```bash
cd frontend
npm ci
npm run build
```

构建产物为 `frontend/dist/`，应由独立静态托管或前端服务发布，不复制进 CloudBase 后端
镜像。前端通过部署时配置的 API 基础地址访问后端；当前代码支持 `VITE_API_BASE_URL`，
实际值需在前端部署平台配置。

`.dockerignore` 排除 `frontend/node_modules/` 和 `frontend/dist/` 是有意设计，用于保持
后端镜像构建上下文轻量，不是遗漏前端构建产物。

### v0.2.0 发布范围

v0.2.0 发布范围包括：

- FastAPI 后端源码；
- React/Vite 前端源码；
- CloudBase 后端部署配置；
- 前端独立构建配置。

该范围不要求 `frontend/dist/` 进入 CloudBase 后端镜像。

云端预览版必须设置：

```dotenv
APP_ENV=production
APP_DEBUG=false
RAG_ENABLED=false
```

实际部署还需要注入以下变量。示例只使用占位符，禁止把真实配置写入 GitHub：

```dotenv
DATABASE_URL=mysql+asyncmy://<database-user>:<url-encoded-password>@<internal-database-host>:3306/<database-name>?charset=utf8mb4
JWT_SECRET_KEY=<long-random-jwt-secret>
DEEPSEEK_API_KEY=<your-deepseek-api-key>
DEEPSEEK_MODEL=deepseek-chat
CORS_ORIGINS=https://<your-domain.example.com>
```

如果数据库密码包含 `@`、`:`、`/`、`#`、`%` 等保留字符，必须先进行 URL 编码，否则
连接字符串可能被错误解析。真实数据库账号、密码、内网地址、API Key、JWT 密钥、访问
凭证和未备案域名不得写入仓库、公开日志或截图。

`RAG_ENABLED=false` 时，知识库上传、模型预热和 RAG 问答接口返回
“云端预览版暂未开放知识库 RAG 功能”，应用不会加载 sentence-transformers、下载
Hugging Face 模型、初始化 Chroma 或创建 `/app/data/chroma`。

CloudBase 使用仓库根目录的 `Dockerfile` 和 `requirements-cloud.txt`。该依赖集只包含
Web API、数据库、认证、PDF 解析以及普通 DeepSeek 对话所需组件，不包含 Torch、CUDA、
NVIDIA、sentence-transformers、Transformers、Chroma 或本地嵌入模型依赖。镜像构建时会
自动执行 `scripts/check_cloud_runtime.py`，验证禁用态导入、健康路由、RAG 503 响应和禁用包
缺失状态。

根目录 `Dockerfile` 的启动命令会先执行 `python -m app.db.startup`，等待数据库、获取 MySQL
迁移锁并执行 Alembic 升级，然后才启动 Uvicorn。手动迁移只用于自动迁移失败后的排查。

## 本地 Docker

本地 Docker Compose 默认设置 `RAG_ENABLED=true`，继续使用命名卷持久化 Chroma 数据和
Hugging Face 模型缓存。Compose 明确使用 `Dockerfile.local` 和完整的 `requirements.txt`，
完整 RAG 开发与演示流程保持不变。

```bash
docker compose up -d --build
```

如需在本地验证云端预览模式，可以临时显式设置 `RAG_ENABLED=false`，但不要把真实密码、
JWT 密钥或 API Key 写入仓库。

## 后续演进

CloudBase 容器本地目录属于临时存储，不适合作为向量数据库的生产持久化层。后续将把
Chroma 本地存储迁移到独立向量数据库服务，再为云端环境启用 `RAG_ENABLED=true` 和
多实例扩缩容。

## 在线预览与本地完整版

CloudBase 在线预览版支持注册登录、文本型 PDF 简历解析、简历与 JD 匹配、普通 AI 对话、
历史记录和 MySQL 持久化；不支持知识库 PDF 上传、Embedding 模型预热、Chroma 检索和
RAG 问答。

本地 Docker 完整版在上述能力之外，还支持 LangChain + Chroma RAG、本地 Embedding
模型、知识库上传、来源引用，以及 Chroma 和 Hugging Face 缓存持久化。

## 健康检查

后端健康检查地址为 `/api/v1/health`，只返回总体状态、数据库状态和 `rag_enabled`，
不会返回数据库地址、密码、API Key 或其他敏感配置。
