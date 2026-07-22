# AiCareer 项目演示操作清单

## 1. 检查记录（2026-07-22）

- 后端执行 `pytest -q`：47 passed，另有 1 条第三方依赖弃用警告。
- `ruff check .`、Python `compileall`、`npm ci` 和前端生产构建均通过。
- Docker 服务状态、前端生产构建和端到端演示流程需要在每次演示前重新检查，本记录不把历史状态作为长期保证。
- Chroma 以嵌入式持久化方式运行在 API 服务内，没有单独的 Compose 服务和对外端口。
- 根目录 CloudBase `Dockerfile` 只构建 FastAPI 后端；React 前端的线上部署方式需要根据实际 CloudBase 服务配置确认。

## 2. 启动命令

在项目根目录执行：

```powershell
docker compose build
docker compose up -d
docker compose ps
```

API 容器启动时会自动等待数据库并执行 Alembic 迁移。只有自动迁移失败或需要单独排查时，
才手动执行：

```powershell
docker compose run --rm api alembic upgrade head
```

日常已构建环境可以简化为：

```powershell
docker compose up -d
docker compose ps
```

## 3. 地址与端口

- 前端工作台：http://localhost:3000
- 后端 API：http://localhost:8000
- Swagger 文档：http://localhost:8000/docs
- MySQL：宿主机 `127.0.0.1:3307`，容器内部 `mysql:3306`
- Redis：宿主机 `localhost:6379`，容器内部 `redis:6379`
- Chroma：API 容器内持久化卷，无宿主机端口

## 4. 本地临时演示账号

- 用户名：`<本地演示用户名>`
- 邮箱：`<虚构演示邮箱>`
- 密码：`<仅在本地设置，不提交仓库>`

演示账号仅应在本地环境临时创建。禁止在公开仓库中保存可用账号、密码或线上测试凭证。

## 5. 演示资料

- 虚构简历：`fictional-python-ai-resume.pdf`
- 岗位 JD：`python-ai-application-developer-jd.txt`
- 知识库资料：`python-ai-interview-guide.pdf`

文件均位于 `output/demo/`。

## 6. 浏览器点击顺序

1. 打开 `http://localhost:3000`。
2. 点击右上角“登录 / 注册”。使用本地临时创建的演示账号登录，不在录屏或截图中展示密码。
3. 点击左侧“简历分析”。
4. 点击“选择文件”，上传 `fictional-python-ai-resume.pdf`。
5. 将 `python-ai-application-developer-jd.txt` 全文粘贴到“粘贴目标岗位 JD”。
6. 点击“开始 AI 匹配分析”，等待出现综合匹配度、匹配技能、待补充技能和简历优化建议。
7. 本地 Docker 完整版可点击左侧“知识库”；CloudBase 在线预览版跳过知识库和 RAG 步骤。
8. 本地 Docker 完整版点击“上传 PDF 资料”，选择 `python-ai-interview-guide.pdf`。
9. 本地 Docker 完整版在右侧问答框输入“这个岗位最看重哪些能力？”，点击纸飞机“提问”。
10. 本地 Docker 完整版展示回答下方“参考来源：python-ai-interview-guide.pdf”。
11. 点击左侧“历史记录”，切换到“分析记录”，打开一条记录查看详情。
12. 本地 Docker 完整版可切换到“RAG 问答”，展示刚才的问题、回答和来源文件。

## 7. 六张截图

截图中的知识库和 RAG 页面来自本地 Docker 完整版，CloudBase 在线预览版暂未开放该功能。
公开使用截图前应再次确认画面没有账号、邮箱、密码、域名、数据库地址或其他环境配置。

1. `screenshots/01-dashboard.png`：登录后的工作台首页。
2. `screenshots/02-resume-and-jd.png`：简历已解析、岗位 JD 已填写、尚未点击分析。
3. `screenshots/03-analysis-result.png`：综合匹配度、匹配技能、缺失技能与建议。
4. `screenshots/04-knowledge-library.png`：知识库资料列表，显示 1 页、2 个知识片段和 Chroma。
5. `screenshots/05-rag-answer-with-source.png`：RAG 回答与来源文件标签。
6. `screenshots/06-history-analysis-detail.png`：历史分析详情，包含评分、技能和修改建议。

## 8. 2～3 分钟视频顺序

- 00:00～00:15：工作台首页，说明系统由 React、FastAPI、MySQL、Redis、Chroma 和 DeepSeek 组成。
- 00:15～00:30：退出后快速登录，说明 JWT 会话与用户数据隔离。
- 00:30～00:55：进入“简历分析”，上传虚构 PDF 简历并粘贴岗位 JD。
- 00:55～01:25：点击“开始 AI 匹配分析”，展示评分、匹配技能、待补充技能和修改建议。
- 01:25～01:45：本地 Docker 完整版进入“知识库”并上传面试准备资料；CloudBase 在线预览版跳过。
- 01:45～02:10：本地 Docker 完整版提问“这个岗位最看重哪些能力？”，重点展示回答引用来源文件。
- 02:10～02:35：进入“历史记录”并打开分析详情；本地 Docker 完整版再切换到“RAG 问答”。
- 02:35～02:50：回到工作台，总结完整业务闭环。

## 9. 已知限制与注意事项

- 仅支持文本型 PDF，不支持扫描件 OCR。
- DeepSeek 生成内容存在非确定性；AI 匹配分只用于辅助判断，不代表真实招聘结论。
- 首次下载或加载 Embedding 模型可能耗时 1～2 分钟；演示前可先预热并保留模型缓存。
- Redis 已接入基础设施，但当前核心功能不依赖缓存命中。
- CloudBase 在线预览版关闭 RAG；不要把本地知识库截图描述成线上功能。
- 当前没有完整 Agent 工作流、运营后台、异步任务队列或多模型路由。
- 前端和后端的线上部署方式以实际 CloudBase 配置为准。
