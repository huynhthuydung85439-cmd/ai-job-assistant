# AI Job Assistant

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

3. 启动接口（MySQL、Redis 可单独通过 Docker 启动）：

   ```bash
   docker compose up -d mysql redis
   uvicorn app.main:app --reload
   ```

4. 访问：

   - API 文档：<http://localhost:8000/docs>
   - 健康检查：<http://localhost:8000/api/v1/health>

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

