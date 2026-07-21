# CloudBase 求职展示预览版配置

## 部署范围

CloudBase 第一版用于求职展示预览。关系数据继续使用 CloudBase MySQL，注册登录、
简历解析、JD 匹配、普通 AI 对话和历史记录保持可用。

云端预览版必须设置：

```dotenv
APP_ENV=production
APP_DEBUG=false
RAG_ENABLED=false
```

`RAG_ENABLED=false` 时，知识库上传、模型预热和 RAG 问答接口返回
“云端预览版暂未开放知识库 RAG 功能”，应用不会加载 sentence-transformers、下载
Hugging Face 模型、初始化 Chroma 或创建 `/app/data/chroma`。

CloudBase 使用仓库根目录的 `Dockerfile` 和 `requirements-cloud.txt`。该依赖集只包含
Web API、数据库、认证、PDF 解析以及普通 DeepSeek 对话所需组件，不包含 Torch、CUDA、
NVIDIA、sentence-transformers、Transformers、Chroma 或本地嵌入模型依赖。镜像构建时会
自动执行 `scripts/check_cloud_runtime.py`，验证禁用态导入、健康路由、RAG 503 响应和禁用包
缺失状态。

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

## 健康检查

后端健康检查地址为 `/api/v1/health`，只返回总体状态、数据库状态和 `rag_enabled`，
不会返回数据库地址、密码、API Key 或其他敏感配置。
