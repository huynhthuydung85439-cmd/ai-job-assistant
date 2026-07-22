# AI 求职助手（AI Job Assistant）

面向求职场景的一站式 AI 工作台，提供简历解析、岗位匹配、智能对话与个人 RAG 知识库能力。

| 项目状态 | 结果 |
| --- | --- |
| 当前版本 | **v0.1.0 MVP**（仓库存在同名 Tag，未创建 GitHub Release） |
| 自动化测试 | 覆盖认证、简历解析、JD 匹配、AI 对话、RAG、历史记录、数据库启动和迁移；最新结果以 `pytest` 或 CI 为准 |
| 部署形态 | 本地 Docker 完整版 + CloudBase 在线预览配置（线上状态需以实际 CloudBase 服务配置确认） |

## 核心功能

- 用户注册登录与 JWT 身份认证
- PDF 简历上传、文本解析与记录保存
- 简历与岗位 JD 智能匹配分析
- 基于 DeepSeek 的 AI 求职对话
- 基于 LangChain + Chroma 的个人 RAG 知识库
- 简历、分析、普通对话与 RAG 问答历史
- API、关系数据与向量检索的用户级数据隔离
- Docker Compose 全栈编排与数据卷持久化

## 技术栈

- **前端：** React + TypeScript（Vite）
- **后端：** FastAPI（Python 3.12）
- **AI 编排：** LangChain
- **大语言模型：** DeepSeek
- **向量数据库：** Chroma
- **关系数据库：** MySQL
- **缓存基础设施：** Redis
- **身份认证：** JWT
- **容器编排：** Docker Compose
- **Web 服务与反向代理：** Nginx

## 项目架构

```mermaid
flowchart LR
    U[用户浏览器] --> W[React / Nginx]
    W --> A[FastAPI]
    A --> D[DeepSeek]
    A --> M[(MySQL)]
    A --> R[(Redis)]
    A --> C[(Chroma)]
```

浏览器通过 Nginx 访问 React 单页应用，并将 `/api` 请求反向代理到 FastAPI。FastAPI 负责认证、业务编排与数据隔离，调用 DeepSeek 完成生成任务，通过 MySQL 保存业务记录，通过 Chroma 保存和检索知识向量；Redis 已纳入 Compose 与连接层，作为缓存基础设施预留。

详细设计见 [docs/architecture.md](docs/architecture.md)。

## 运行版本边界

| 能力 | CloudBase 在线预览版 | 本地 Docker 完整版 |
| --- | --- | --- |
| 注册与登录、文本型 PDF 简历解析 | 支持 | 支持 |
| 简历与 JD 匹配、普通 AI 对话、历史记录 | 支持 | 支持 |
| MySQL 数据持久化 | 支持 | 支持 |
| 知识库 PDF 上传、Embedding 预热 | 暂不支持 | 支持 |
| Chroma 检索、RAG 问答和来源引用 | 暂不支持 | 支持 |

CloudBase 在线预览版设置 `RAG_ENABLED=false`；本地 Docker Compose 默认设置
`RAG_ENABLED=true`，并持久化 Chroma 数据与 Hugging Face 模型缓存。前端和后端的
实际线上部署方式需根据 CloudBase 服务配置确认，不能仅由仓库代码推断。

## 功能说明

### 用户注册登录

用户可使用用户名、邮箱和密码注册，通过登录接口获取 JWT。受保护的接口从 Bearer Token 识别当前用户，密码仅以 bcrypt 哈希形式保存。

### PDF 简历解析

支持上传不超过 10 MB 的文本型 PDF 简历，解析文件名、页数和正文。登录用户的解析结果会保存到 MySQL，供后续分析与历史查看使用。

### 简历与 JD 匹配

将简历正文与岗位描述提交给 AI，返回 0–100 匹配分、匹配技能、缺失技能、简历优化建议和可能的面试问题。登录用户可将结果关联到自己的简历记录。

### AI 对话

通过 LangChain 调用 DeepSeek，提供通用求职问答。登录状态下的对话会保存到个人历史记录。

### RAG 知识库

登录用户可上传招聘 JD、面试资料等 PDF。系统解析并切分文本，生成向量后写入持久化 Chroma；提问时只检索当前用户的文档，并返回答案及来源文件。

本地 Docker Compose 默认设置 `RAG_ENABLED=true`，保留完整的模型下载、Chroma
持久化和知识库功能。CloudBase 求职展示预览版设置 `RAG_ENABLED=false`，暂时关闭
知识库上传、预热和 RAG 问答，注册登录、简历解析、JD 匹配、普通 AI 对话及历史记录
不受影响。后续版本将迁移到独立向量数据库服务后再开放云端 RAG。

### 历史记录

工作台按分类展示当前用户的简历、匹配分析、普通 AI 对话和 RAG 问答，列表接口支持分页，分析记录支持查看详情。

### 用户数据隔离

所有现有资源查询均按当前用户隔离；分析详情和知识文档删除会校验资源所有权。简历、分析记录和聊天记录的删除能力暂未开放。

### Docker 持久化

Compose 使用命名卷保存 MySQL、Redis、Chroma 和 Hugging Face 模型缓存。重建应用容器不会清空这些数据；如需删除数据卷，必须显式执行带 `--volumes` 的停机操作。

## 项目截图

以下截图来自仓库中的本地演示资料，使用虚构简历和岗位内容，不包含可用登录凭证。

![简历与 JD 输入](output/demo/screenshots/02-resume-and-jd.png)

![历史分析详情](output/demo/screenshots/06-history-analysis-detail.png)

知识库和 RAG 相关截图来自本地 Docker 完整版；CloudBase 在线预览版暂未开放这些功能。

## Docker 快速启动

### 1. 准备配置

```bash
cp .env.example .env
```

Windows PowerShell：

```powershell
Copy-Item .env.example .env
```

在 `.env` 中替换所有占位符，至少设置数据库密码、JWT 签名密钥和 DeepSeek API Key。不要提交 `.env`。

### 2. 启动全栈

```bash
docker compose up -d --build
```

API 容器启动时会自动等待数据库并执行 Alembic 迁移。只有自动迁移失败或需要单独排查时，才手动执行：

```bash
docker compose run --rm api alembic upgrade head
```

启动后可访问：

- Web 工作台：<http://localhost:3000>
- FastAPI：<http://localhost:8000>
- API 文档（非生产环境）：<http://localhost:8000/docs>

查看服务状态：

```bash
docker compose ps
```

完整演示流程见 [docs/demo-guide.md](docs/demo-guide.md)。

## 环境变量

仓库提供 `.env.example`。以下示例仅使用占位符，必须按实际部署环境替换：

```dotenv
APP_ENV=development
APP_DEBUG=false
APP_PORT=8000
WEB_PORT=3000

MYSQL_DATABASE=<database-name>
MYSQL_USER=<database-user>
MYSQL_PASSWORD=<database-password>
MYSQL_ROOT_PASSWORD=<database-password>
DATABASE_URL=mysql+asyncmy://<database-user>:<url-encoded-password>@<internal-database-host>:3306/<database-name>?charset=utf8mb4

REDIS_URL=redis://redis:6379/0

JWT_SECRET_KEY=<long-random-jwt-secret>
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

DEEPSEEK_API_KEY=<your-deepseek-api-key>
DEEPSEEK_MODEL=deepseek-chat

RAG_ENABLED=true
CHROMA_PERSIST_DIRECTORY=/app/data/chroma
CHROMA_COLLECTION_NAME=job_assistant_knowledge
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
RAG_CHUNK_SIZE=800
RAG_CHUNK_OVERLAP=120
RAG_TOP_K=4
```

安全要求：

- 禁止提交 `.env`、API Key、JWT 签名密钥、数据库密码或访问令牌。
- 每个环境应使用独立且足够长的随机 `JWT_SECRET_KEY`。
- 生产环境应关闭调试模式，并通过外部密钥管理方案注入敏感变量。
- 数据库密码包含 `@`、`:`、`/`、`#`、`%` 等字符时，必须先进行 URL 编码再写入 `DATABASE_URL`。

## 本地开发

后端：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
docker compose up -d mysql redis
alembic upgrade head
uvicorn app.main:app --reload
```

前端：

```bash
cd frontend
npm install
npm run dev
```

Vite 开发服务器默认为 <http://localhost:5173>，并将 `/api` 请求代理到本地 FastAPI。

## 项目结构

```text
app/                         FastAPI 应用、业务服务、模型与 RAG
frontend/                    React + TypeScript 前端与 Nginx 配置
migrations/                  Alembic 数据库迁移
tests/                       pytest 自动化测试
docs/                        架构、演示与面试说明
docker-compose.yml           全栈服务与持久卷编排
```

## 质量检查

自动化测试覆盖认证、简历解析、JD 匹配、AI 对话、RAG、历史记录、数据库启动和迁移。最新测试结果请以 `pytest` 或 CI 状态为准。

```bash
pytest -q
ruff check .
python -m compileall -q app tests migrations
cd frontend && npm run build
```

## 项目文档

- [架构说明](docs/architecture.md)
- [CloudBase 预览版部署配置](docs/deploy-cloudbase.md)
- [演示指南](docs/demo-guide.md)
- [面试讲解笔记](docs/interview-notes.md)

## 版本说明

当前代码以 `v0.1.0 MVP` 描述。仓库存在 `v0.1.0` Tag，但没有对应的 GitHub Release；CloudBase 在线服务是否可用及其前后端部署方式需以实际服务配置为准。

## 已知限制

- 仅支持文本型 PDF，不支持扫描件 OCR。
- AI 匹配分只用于辅助判断，不代表真实招聘结论。
- Redis 已接入基础设施，但当前核心功能不依赖缓存命中。
- CloudBase 在线预览版关闭 RAG；完整知识库能力仅在本地 Docker 版提供。
- 当前没有完整 Agent 工作流，也没有工具调用、自动规划或循环决策能力。
- 当前没有运营后台、异步任务队列和多模型路由。
- 前端和后端的线上部署方式以实际 CloudBase 配置为准。
