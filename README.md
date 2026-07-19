# AI Job Assistant

基于 React、FastAPI、LangChain、DeepSeek 和 Chroma 的 AI 求职助手。目前支持 AI 对话、PDF 简历解析、简历与岗位 JD 匹配分析、RAG 知识库，以及 JWT 用户认证与 MySQL 数据持久化。

## 技术栈

- Python 3.12
- React / TypeScript / Vite
- FastAPI
- LangChain / LangGraph / DeepSeek
- SQLAlchemy 2 / Alembic / MySQL 8.4
- Chroma / Redis
- Docker / Docker Compose

## 项目结构

```text
app/
├── api/                    # API 版本与基础路由
├── core/                   # 配置、JWT、安全与异常处理
├── db/                     # SQLAlchemy Base 与异步会话
├── dependencies/           # FastAPI 认证依赖
├── models/                 # User、Resume、AnalysisRecord、ChatHistory、KnowledgeDocument
├── rag/                    # 文档加载、向量库、检索与 RAG 服务
├── routers/                # auth、resume、knowledge、history 路由
├── schemas/                # 请求与响应模型
├── services/               # 对话、认证、PDF、分析与记录服务
└── main.py                 # FastAPI 应用入口
migrations/                 # Alembic 数据库迁移
tests/                      # pytest 自动化测试
frontend/                   # React 求职工作台
```

## 配置

复制环境变量模板：

```powershell
Copy-Item .env.example .env
```

至少设置以下配置：

```dotenv
DATABASE_URL=mysql+asyncmy://ai_job_user:change_me@localhost:3306/ai_job_assistant?charset=utf8mb4
JWT_SECRET_KEY=请替换为足够长的随机字符串
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
BCRYPT_ROUNDS=12

DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_MODEL=deepseek-chat
```

不要将 `.env` 或任何真实密钥提交到 Git。生产环境应使用独立、足够长的 `JWT_SECRET_KEY`。

## 本地启动

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt

docker compose up -d mysql redis
alembic upgrade head
uvicorn app.main:app --reload
```

服务默认地址为 <http://localhost:8000>，接口文档为 <http://localhost:8000/docs>。

前端开发模式：

```powershell
cd frontend
npm install
npm run dev
```

前端地址为 <http://localhost:5173>。Vite 会将 `/api` 请求代理到本地 FastAPI 服务。

### UI 设计参考

前端视觉语言参考 Figma Community 的 [AiDEA – Smart SaaS Dashboard UI Kit](https://www.figma.com/community/file/1532723729743223601)（Hamed，CC BY 4.0）。本项目重新实现了适合 AI 求职场景的页面与组件，没有复制该套件的付费素材。

## 用户注册与登录

注册用户：

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "email": "alice@example.com",
    "password": "secure-password"
  }'
```

登录并获取 JWT：

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"secure-password"}'
```

响应示例：

```json
{
  "token": "eyJ...",
  "user_id": 1
}
```

访问支持认证的接口时通过 Bearer Header 携带 JWT：

```http
Authorization: Bearer eyJ...
```

普通 chat 与不保存记录的 resume 操作仍支持匿名访问；知识库及历史记录接口必须携带有效 JWT。认证后：

- PDF 简历上传会写入 `resumes` 表并额外返回 `resume_id`。
- 简历分析请求携带 `resume_id` 时会写入 `analysis_records` 表。
- 普通 AI 对话与 RAG 问答会按类型写入 `chat_histories` 表。
- 知识库文件元数据会写入 `knowledge_documents` 表，向量按用户隔离检索。

前端把 JWT 会话保存在浏览器本地存储中，并在启动时通过 `/api/v1/auth/me` 校验。会话校验完成前不会改变当前深层路由。

## AI 对话

```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message":"帮我分析这个岗位"}'
```

响应：

```json
{
  "answer": "..."
}
```

## PDF 简历上传与分析保存

上传不超过 10 MB 的文本型 PDF：

```bash
curl -X POST "http://localhost:8000/api/v1/resume/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@resume.pdf;type=application/pdf"
```

认证请求的响应示例：

```json
{
  "filename": "resume.pdf",
  "text": "Python、FastAPI 项目经验……",
  "pages": 2,
  "resume_id": 1
}
```

将上传结果中的 `text` 和 `resume_id` 用于分析：

```bash
curl -X POST "http://localhost:8000/api/v1/resume/analyze" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "resume_id": 1,
    "resume_text": "Python、FastAPI 项目经验……",
    "job_description": "招聘 Python 工程师，要求 FastAPI、MySQL 和 Kubernetes"
  }'
```

`resume_id` 只能由所属用户使用；匿名分析仍可省略该字段，返回结构与原接口一致。

## RAG 知识库

上传招聘 JD 或面试资料 PDF：

```bash
curl -X POST "http://localhost:8000/api/v1/knowledge/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@job-description.pdf;type=application/pdf"
```

查看当前用户已登记的知识库文件：

```bash
curl "http://localhost:8000/api/v1/knowledge/documents?page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN"
```

基于知识库提问：

```bash
curl -X POST "http://localhost:8000/api/v1/knowledge/chat" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"question":"这个岗位需要哪些技能？"}'
```

RAG 使用单例复用的本地多语言 Embedding 模型与持久化 Chroma，默认数据目录为 `data/chroma`。

### 演示前预热

首次使用会下载并加载 Embedding 模型，耗时取决于网络与机器性能。演示前登录并调用一次受保护的预热接口：

```bash
curl -X POST "http://localhost:8000/api/v1/knowledge/warmup" \
  -H "Authorization: Bearer $TOKEN"
```

返回 `{"status":"ready", ...}` 后再上传或问答。Docker 环境中的模型缓存保存在 `huggingface_cache` volume；本地模型文件、`.cache` 和 `data/chroma` 均不应提交 Git。

## 历史记录接口

以下接口均要求 Bearer JWT，支持 `page` 和 `page_size` 参数，并且只返回当前用户的数据：

- `GET /api/v1/history/resumes`：简历列表，不返回完整简历正文。
- `GET /api/v1/history/analyses`：分析记录列表。
- `GET /api/v1/history/analyses/{analysis_id}`：分析详情。
- `GET /api/v1/history/chats`：普通 AI 对话记录。
- `GET /api/v1/history/rag-chats`：RAG 问答与 sources。

## 数据库表与迁移

- `users`：用户、唯一用户名/邮箱、bcrypt 密码哈希。
- `resumes`：用户上传的 PDF 文件名与解析文本，通过 `user_id` 关联用户。
- `analysis_records`：结构化分析结果，通过 `resume_id` 关联简历。
- `chat_histories`：用户的普通对话和 RAG 问答记录，保存类型及 RAG sources。
- `knowledge_documents`：知识库文件名、页数、分块数量、集合标识和向量 ID 登记。

外键均启用 `ON DELETE CASCADE`。执行迁移：

```bash
alembic upgrade head
```

创建后续迁移：

```bash
alembic revision --autogenerate -m "describe change"
```

## Docker 启动

```bash
docker compose build
docker compose run --rm api alembic upgrade head
docker compose up -d --build
```

Compose 会启动 Web、API、MySQL 和 Redis。Web 工作台地址为 <http://localhost:3000>，并持久化 MySQL、Redis、Chroma 与模型缓存数据。

## 质量检查

```bash
pytest -q
ruff check .
python -m compileall -q app tests migrations
cd frontend && npm run build
```
