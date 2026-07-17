# AI Job Assistant

AI-powered job assistant based on LLM, RAG and Agent technology.

基于 FastAPI、LangChain 与 LangGraph 的 AI 求职助手后端项目骨架。

## 规划能力

- 简历分析
- JD 岗位匹配
- AI 面试模拟
- Prompt 管理
- RAG 知识库（后续扩展）

当前仓库只包含可运行的基础设施与模块边界，不包含具体业务实现。

## 技术栈

- Python 3.12
- FastAPI
- LangChain / LangGraph
- MySQL 8.4
- Redis 7
- SQLAlchemy 2 / Alembic
- Docker / Docker Compose

## 项目结构

```text
.
├── app/
│   ├── ai/                    # LangChain、LangGraph、Prompt 与未来 RAG
│   ├── api/                   # HTTP API 与版本路由
│   ├── cache/                 # Redis 基础设施
│   ├── core/                  # 配置、日志等横切能力
│   ├── db/                    # SQLAlchemy 会话与模型基类
│   ├── modules/               # 按业务能力划分的模块边界
│   ├── schemas/               # 公共请求/响应模型
│   └── main.py                # FastAPI 应用入口
├── migrations/                # Alembic 数据库迁移
├── tests/                     # 自动化测试
├── .env.example               # 环境变量示例
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml             # 工具配置
└── requirements.txt
```

## 本地启动

1. 创建虚拟环境并安装依赖：

   ```bash
   python -m venv .venv
   # Windows PowerShell
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

2. 准备配置：

   ```bash
   Copy-Item .env.example .env
   ```

   编辑 `.env`，填写从 DeepSeek 控制台获取的密钥：

   ```dotenv
   DEEPSEEK_API_KEY=your_deepseek_api_key
   ```

3. 启动接口（MySQL、Redis 可单独通过 Docker 启动）：

   ```bash
   docker compose up -d mysql redis
   uvicorn app.main:app --reload
   ```

4. 访问：

   - API 文档：<http://localhost:8000/docs>
   - 健康检查：<http://localhost:8000/api/v1/health>

## AI 对话接口

```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message":"帮我分析这个岗位"}'
```

响应示例：

```json
{
  "answer": "请提供岗位描述，我会从职责、要求和匹配度进行分析。"
}
```

## 简历智能分析接口

提交简历文本和目标岗位 JD：

```bash
curl -X POST "http://localhost:8000/api/v1/resume/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "三年 Python 和 FastAPI 开发经验。",
    "job_description": "招聘 Python 工程师，要求 FastAPI、MySQL 和 Kubernetes。"
  }'
```

响应示例：

```json
{
  "score": 85,
  "matching_skills": ["Python", "FastAPI"],
  "missing_skills": ["Kubernetes"],
  "resume_advices": ["补充项目成果和性能指标"],
  "interview_questions": ["如何设计高可用的 FastAPI 服务？"]
}
```

## PDF 简历上传接口

上传最大 10 MB 的文本型 PDF 简历：

```bash
curl -X POST "http://localhost:8000/api/v1/resume/upload" \
  -F "file=@resume.pdf;type=application/pdf"
```

响应示例：

```json
{
  "filename": "resume.pdf",
  "text": "Python、FastAPI 项目经验……",
  "pages": 2
}
```

如需继续分析，将响应中的 `text` 作为 `resume_text`，与目标岗位
`job_description` 一起提交到 `/api/v1/resume/analyze`。当前版本提取文本型 PDF；
扫描件需要后续接入 OCR。

## Docker 启动

```bash
docker compose up --build
```

服务默认监听 <http://localhost:8000>。Compose 会等待 MySQL 与 Redis 健康后再启动 API。

## 数据库迁移

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

## 质量检查

```bash
ruff check .
ruff format --check .
pytest
```

## 配置约定

配置统一从环境变量读取，本地可使用 `.env`。不要提交真实密钥；新增配置时同步更新 `.env.example` 和 `app/core/config.py`。

