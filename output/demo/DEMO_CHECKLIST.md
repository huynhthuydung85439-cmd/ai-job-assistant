# AiCareer 项目演示操作清单

## 1. 当前检查结论

- Docker Desktop、Docker Engine、Docker Compose 正常。
- `web`、`api`、`mysql`、`redis` 均为 `healthy`。
- 前端生产构建通过；后端 31 项 pytest 通过；Ruff 通过。
- 注册、登录、工作台、PDF 简历上传、JD 输入、简历分析、结构化结果、知识库上传、RAG 引用、历史记录均已实际走通。
- Chroma 以嵌入式持久化方式运行在 API 服务内，没有单独的 Compose 服务和对外端口。

## 2. 启动命令

在项目根目录执行：

```powershell
docker compose build
docker compose run --rm api alembic upgrade head
docker compose up -d
docker compose ps
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

## 4. 安全演示账号

- 用户名：`demo_showcase_20260719`
- 邮箱：`demo@aicareer-demo.com`（虚构演示地址）
- 密码：`Demo-Showcase-2026!`

以上信息仅用于本地演示，不对应真实人员或真实邮箱。不要在真实环境复用该密码。

## 5. 演示资料

- 虚构简历：`fictional-python-ai-resume.pdf`
- 岗位 JD：`python-ai-application-developer-jd.txt`
- 知识库资料：`python-ai-interview-guide.pdf`

文件均位于 `output/demo/`。

## 6. 浏览器点击顺序

1. 打开 `http://localhost:3000`。
2. 点击右上角“登录 / 注册”。演示登录时输入上面的用户名和密码，点击“安全登录”。
3. 点击左侧“简历分析”。
4. 点击“选择文件”，上传 `fictional-python-ai-resume.pdf`。
5. 将 `python-ai-application-developer-jd.txt` 全文粘贴到“粘贴目标岗位 JD”。
6. 点击“开始 AI 匹配分析”，等待出现综合匹配度、匹配技能、待补充技能和简历优化建议。
7. 点击左侧“知识库”。若首次进入显示模型加载，请等待页面恢复可输入状态。
8. 点击“上传 PDF 资料”，选择 `python-ai-interview-guide.pdf`。
9. 在右侧问答框输入“这个岗位最看重哪些能力？”，点击纸飞机“提问”。
10. 展示回答下方“参考来源：python-ai-interview-guide.pdf”。
11. 点击左侧“历史记录”，切换到“分析记录”，点击 88 分记录查看详情。
12. 切换到“RAG 问答”，展示刚才的问题、回答和来源文件。

## 7. 六张截图

1. `screenshots/01-dashboard.png`：登录后的工作台首页。
2. `screenshots/02-resume-and-jd.png`：简历已解析、岗位 JD 已填写、尚未点击分析。
3. `screenshots/03-analysis-result.png`：88 分综合匹配度、匹配技能、缺失技能与建议。
4. `screenshots/04-knowledge-library.png`：知识库资料列表，显示 1 页、2 个知识片段和 Chroma。
5. `screenshots/05-rag-answer-with-source.png`：RAG 回答与来源文件标签。
6. `screenshots/06-history-analysis-detail.png`：历史分析详情，包含评分、技能和修改建议。

## 8. 2～3 分钟视频顺序

- 00:00～00:15：工作台首页，说明系统由 React、FastAPI、MySQL、Redis、Chroma 和 DeepSeek 组成。
- 00:15～00:30：退出后快速登录，说明 JWT 会话与用户数据隔离。
- 00:30～00:55：进入“简历分析”，上传虚构 PDF 简历并粘贴岗位 JD。
- 00:55～01:25：点击“开始 AI 匹配分析”，展示评分、匹配技能、待补充技能和修改建议。
- 01:25～01:45：进入“知识库”，上传面试准备资料。
- 01:45～02:10：提问“这个岗位最看重哪些能力？”，重点展示回答引用来源文件。
- 02:10～02:35：进入“历史记录”，打开分析详情，再切换到“RAG 问答”。
- 02:35～02:50：回到工作台，总结完整业务闭环。

## 9. 当前异常与注意事项

- 未发现阻塞演示的核心功能异常。
- DeepSeek 生成内容存在非确定性；本次 88 分结果中有一条关于项目日期的判断不准确，属于模型内容质量问题，不影响结构化输出和保存流程。
- 首次下载或加载 Embedding 模型可能耗时 1～2 分钟；当前环境已经预热并缓存。
- 演示账号已包含用于截图的多条安全测试记录，便于直接展示历史页面。
- MySQL 启动日志包含自签名 CA 和时区数据警告，不影响当前演示功能。
- 无效邮箱的前端错误提示已从 `[object Object]` 修正为可读校验信息；历史页重复“记录”文案已修正。
