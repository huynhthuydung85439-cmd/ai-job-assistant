# AI 求职助手演示指南

## 1. 演示目标

建议用 6–10 分钟展示“注册登录 → 简历解析 → JD 匹配 → AI 对话 → RAG 知识库 → 历史记录”的完整闭环，重点说明 AI 能力、数据持久化和用户隔离。

## 2. 演示前准备

- Docker Desktop 已启动，`docker compose version` 可正常执行。
- 已将 `.env.example` 复制为 `.env`。
- `.env` 中只在本机填写有效配置，不在录屏、截图、终端输出或 Git 提交中展示密钥。
- 准备一份不含真实隐私信息的文本型 PDF 示例简历。
- 准备一份示例岗位 JD，以及一份面试资料或岗位说明 PDF。

配置示意（仅占位符）：

```dotenv
MYSQL_DATABASE=<database-name>
MYSQL_USER=<database-user>
MYSQL_PASSWORD=<database-password>
MYSQL_ROOT_PASSWORD=<database-root-password>
JWT_SECRET_KEY=<long-random-jwt-signing-secret>
DEEPSEEK_API_KEY=<your-deepseek-api-key>
DEEPSEEK_MODEL=<deepseek-model-name>
```

## 3. 启动与检查

构建并启动完整服务：

```bash
docker compose up -d --build
```

首次启动或迁移版本变化后执行：

```bash
docker compose run --rm api alembic upgrade head
```

检查服务：

```bash
docker compose ps
```

预期看到 `web`、`api`、`mysql`、`redis` 四个服务运行，其中带健康检查的服务应进入 healthy 状态。浏览器打开：

- 工作台：<http://localhost:3000>
- 健康检查：<http://localhost:8000/api/v1/health>
- API 文档：<http://localhost:8000/docs>（非生产环境）

## 4. 首次 RAG 预热

Embedding 模型首次运行可能需要下载和加载。建议在正式演示前登录工作台，进入知识库页面完成一次预热，等待界面显示就绪后再上传资料。模型缓存保存在 Docker volume，后续容器重建通常无需重新下载。

## 5. 推荐演示脚本

### 场景一：注册与登录（约 1 分钟）

1. 注册一个仅用于演示的账号。
2. 登录后刷新页面，说明前端会通过 `/auth/me` 校验 JWT 会话。
3. 指出知识库和历史记录仅对登录用户开放。

讲解重点：密码以 bcrypt 哈希保存；后端从 JWT 识别当前用户，而不是相信前端传入的用户 ID。

### 场景二：PDF 简历解析（约 1 分钟）

1. 进入简历分析页面。
2. 上传示例 PDF 简历。
3. 展示解析出的文件信息和简历正文。

讲解重点：系统校验 PDF 类型与 10 MB 大小限制；登录用户的解析结果会持久化。

### 场景三：简历与 JD 匹配（约 2 分钟）

1. 粘贴示例岗位 JD。
2. 发起分析。
3. 展示匹配分、匹配技能、缺失技能、简历建议和面试问题。

讲解重点：LangChain 负责模型调用编排，DeepSeek 返回结构化结果；分析记录与当前用户的简历关联。

### 场景四：AI 对话（约 1 分钟）

1. 进入 AI 对话页。
2. 提问：“根据后端开发岗位，帮我制定一周面试准备计划。”
3. 展示回答，并说明登录用户的对话会写入历史记录。

### 场景五：RAG 知识库（约 2 分钟）

1. 上传示例岗位说明或面试资料 PDF。
2. 等待文档解析、切分和向量写入完成。
3. 提问：“这个岗位最看重哪些技能？”
4. 展示回答及来源文件。

讲解重点：Chroma 保存向量；检索通过 `user_id` 过滤；生成答案同时保留来源，降低脱离资料回答的风险。

### 场景六：历史记录与持久化（约 1 分钟）

1. 打开历史记录页，依次查看简历、分析、普通对话和 RAG 问答。
2. 刷新页面或重启应用容器，再次查看记录。
3. 说明 MySQL、Chroma、Redis 和模型缓存分别使用命名卷。

讲解重点：容器生命周期与数据生命周期分离，重建 Web/API 容器不会清空业务数据。

## 6. 用户隔离演示（可选）

1. 使用账号 A 上传一份简历和知识资料。
2. 退出后注册账号 B。
3. 查看账号 B 的历史与知识库，确认无法看到账号 A 的数据。
4. 如演示 API，可说明所有详情和删除操作也会校验资源所有权。

## 7. 常见问题排查

### Docker 无法连接

先确认 Docker Desktop 已启动，再执行：

```bash
docker compose version
docker compose ps
```

### 数据表不存在

执行迁移：

```bash
docker compose run --rm api alembic upgrade head
```

### AI 调用失败

检查本机 `.env` 中的 DeepSeek 配置是否已替换占位符，并查看 API 日志。不要把日志中的授权信息粘贴到公开 issue 或演示画面。

```bash
docker compose logs --tail=100 api
```

### RAG 首次响应较慢

首次使用需要加载 Embedding 模型。提前预热，并保留 `huggingface_cache` volume。

### PDF 无法解析

确认文件是文本型 PDF、大小不超过 10 MB。纯扫描图片 PDF 不属于 v0.1.0 的 OCR 支持范围。

## 8. 演示结束

停止容器但保留数据卷：

```bash
docker compose down
```

不要在需要保留演示数据时使用 `docker compose down --volumes`。
