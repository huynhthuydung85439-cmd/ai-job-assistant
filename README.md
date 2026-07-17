# AI Job Assistant

基于 FastAPI、LangChain、DeepSeek 和 Chroma 的 AI 求职助手后端。目前支持 AI 对话、PDF 简历解析、简历与岗位 JD 匹配分析、RAG 知识库，以及 JWT 用户认证与 MySQL 数据持久化。

## 技术栈

- Python 3.12
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
├── models/                 # User、Resume、AnalysisRecord、ChatHistory
├── rag/                    # 文档加载、向量库、检索与 RAG 服务
├── routers/                # auth、resume、knowledge 路由
├── schemas/                # 请求与响应模型
├── services/               # 对话、认证、PDF、分析与记录服务
└── main.py                 # FastAPI 应用入口
migrations/                 # Alembic 数据库迁移
tests/                      # pytest 自动化测试
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

现有 chat、resume 和 RAG 接口仍支持匿名访问。携带有效 JWT 后：

- PDF 简历上传会写入 `resumes` 表并额外返回 `resume_id`。
- 简历分析请求携带 `resume_id` 时会写入 `analysis_records` 表。
- 普通 AI 对话与 RAG 问答会写入 `chat_histories` 表。

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
  -F "file=@job-description.pdf;type=application/pdf"
```

基于知识库提问：

```bash
curl -X POST "http://localhost:8000/api/v1/knowledge/chat" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"question":"这个岗位需要哪些技能？"}'
```

RAG 使用本地多语言 Embedding 模型与持久化 Chroma，默认数据目录为 `data/chroma`。

## 数据库表与迁移

- `users`：用户、唯一用户名/邮箱、bcrypt 密码哈希。
- `resumes`：用户上传的 PDF 文件名与解析文本，通过 `user_id` 关联用户。
- `analysis_records`：结构化分析结果，通过 `resume_id` 关联简历。
- `chat_histories`：用户的普通对话和 RAG 问答记录。

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
docker compose up --build
```

Compose 会启动 API、MySQL 和 Redis，并持久化 MySQL、Redis、Chroma 与模型缓存数据。

## 质量检查

```bash
pytest -q
ruff check .
python -m compileall -q app tests migrations
```
