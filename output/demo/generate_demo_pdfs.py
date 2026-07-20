# ruff: noqa: E501 - long Chinese copy stays contiguous for PDF text extraction.

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parent
FONT_REGULAR = r"C:\Windows\Fonts\msyh.ttc"
FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
pdfmetrics.registerFont(TTFont("DemoSans", FONT_REGULAR))
pdfmetrics.registerFont(TTFont("DemoSansBold", FONT_BOLD))


def styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "TitleCN",
            parent=base["Title"],
            fontName="DemoSansBold",
            fontSize=22,
            leading=30,
            textColor=colors.HexColor("#16213E"),
            alignment=TA_CENTER,
            spaceAfter=8,
        ),
        "subtitle": ParagraphStyle(
            "SubtitleCN",
            parent=base["Normal"],
            fontName="DemoSans",
            fontSize=10,
            leading=16,
            textColor=colors.HexColor("#6B7280"),
            alignment=TA_CENTER,
            spaceAfter=14,
        ),
        "heading": ParagraphStyle(
            "HeadingCN",
            parent=base["Heading2"],
            fontName="DemoSansBold",
            fontSize=13,
            leading=20,
            textColor=colors.HexColor("#5B4BDB"),
            spaceBefore=10,
            spaceAfter=5,
        ),
        "body": ParagraphStyle(
            "BodyCN",
            parent=base["BodyText"],
            fontName="DemoSans",
            fontSize=9.5,
            leading=16,
            textColor=colors.HexColor("#273043"),
            wordWrap="CJK",
            spaceAfter=3,
        ),
        "small": ParagraphStyle(
            "SmallCN",
            parent=base["BodyText"],
            fontName="DemoSans",
            fontSize=8,
            leading=13,
            textColor=colors.HexColor("#6B7280"),
            wordWrap="CJK",
        ),
    }


def footer(canvas, document):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#E5E7EB"))
    canvas.line(20 * mm, 16 * mm, A4[0] - 20 * mm, 16 * mm)
    canvas.setFont("DemoSans", 7.5)
    canvas.setFillColor(colors.HexColor("#7B8190"))
    canvas.drawString(20 * mm, 10 * mm, "AiCareer 项目演示专用 - 内容完全虚构")
    canvas.drawRightString(A4[0] - 20 * mm, 10 * mm, f"第 {document.page} 页")
    canvas.restoreState()


def document(path):
    return SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=17 * mm,
        bottomMargin=22 * mm,
        title="AiCareer 演示资料",
        author="Fictional Demo Data",
    )


def build_resume():
    s = styles()
    story = [
        Paragraph("匿名候选人 A-017", s["title"]),
        Paragraph("Python / AI 应用开发工程师 · 2 年项目实践 · 演示用虚构简历", s["subtitle"]),
    ]
    facts = [
        [
            Paragraph("求职方向", s["small"]),
            Paragraph("Python 后端、RAG 应用、AI 工程化", s["body"]),
        ],
        [
            Paragraph("核心技术", s["small"]),
            Paragraph(
                "Python、FastAPI、LangChain、Chroma、MySQL、Redis、Docker、React/TypeScript",
                s["body"],
            ),
        ],
    ]
    table = Table(facts, colWidths=[28 * mm, 137 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F5F3FF")),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#DDD6FE")),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E9E5FF")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.extend(
        [
            table,
            Paragraph("个人概述", s["heading"]),
            Paragraph(
                "具备 Python 异步 Web 服务和大模型应用开发经验，能够独立完成从需求拆解、API 设计、数据库建模到 Docker 部署的完整流程。重视可测试性、异常处理与数据隐私。",
                s["body"],
            ),
            Paragraph("项目经历", s["heading"]),
            Paragraph("<b>智能求职助手（核心开发）</b>　2025.10 - 2026.06", s["body"]),
            Paragraph(
                "- 使用 FastAPI 与 SQLAlchemy 构建 JWT 注册登录、PDF 简历解析、岗位匹配分析和历史记录接口。<br/>"
                "- 基于 LangChain、HuggingFace Embedding 与 Chroma 实现按用户隔离的 RAG 知识库，回答中返回来源文件。<br/>"
                "- 使用 MySQL 持久化用户、简历与分析记录，使用 Redis 支撑缓存与服务扩展。<br/>"
                "- 通过 Docker Compose 编排 Web、API、MySQL、Redis 服务；编写 pytest 覆盖上传、分析和知识库流程。<br/>"
                "- 与 React / TypeScript 前端完成接口联调，统一加载状态、错误提示和结果展示。",
                s["body"],
            ),
            Paragraph("另一项实践", s["heading"]),
            Paragraph(
                "<b>内部文档问答原型</b>　2025.04 - 2025.08<br/>"
                "将 PDF 文档切分为带来源元数据的文本块，完成向量化、Top-K 检索与提示词拼接；为模型调用增加超时、重试与空结果处理。",
                s["body"],
            ),
            Paragraph("技能清单", s["heading"]),
            Paragraph(
                "- 后端：Python、FastAPI、Pydantic、SQLAlchemy、RESTful API<br/>"
                "- AI：LangChain、RAG、Embedding、Chroma、结构化输出、Prompt 设计<br/>"
                "- 数据与工程：MySQL、Redis、Docker Compose、Git、pytest、Ruff<br/>"
                "- 协作：React / TypeScript 接口联调、技术文档与问题排查",
                s["body"],
            ),
            Paragraph("待提升方向", s["heading"]),
            Paragraph(
                "尚无 Kubernetes 生产部署与大型 CI/CD 流水线经验；希望在目标岗位中继续补齐云原生发布、可观测性和性能压测能力。",
                s["body"],
            ),
        ]
    )
    document(ROOT / "fictional-python-ai-resume.pdf").build(
        story, onFirstPage=footer, onLaterPages=footer
    )


def build_knowledge():
    s = styles()
    story = [
        Paragraph("Python / AI 应用开发岗位面试准备指南", s["title"]),
        Paragraph("AiCareer 知识库演示资料 · 版本 DEMO-2026.07", s["subtitle"]),
        Paragraph("一、岗位最看重的能力", s["heading"]),
        Paragraph(
            "该岗位优先考察四类能力：第一，使用 Python 与 FastAPI 设计可靠的异步 API；第二，理解 Embedding、向量检索和 RAG 链路；第三，能够使用 MySQL、Redis 与 Docker 完成工程化交付；第四，具备测试、日志、异常处理和安全意识。",
            s["body"],
        ),
        Paragraph("二、RAG 项目讲解要点", s["heading"]),
        Paragraph(
            "候选人应能说明：PDF 如何解析与分块；chunk size 与 overlap 如何影响召回；向量如何写入 Chroma；如何按 user_id 做数据隔离；Top-K 检索结果如何拼接为上下文；回答为什么要返回来源文件；当资料不足时如何避免模型编造。",
            s["body"],
        ),
        Paragraph("三、推荐的项目案例结构", s["heading"]),
        Paragraph(
            "建议用 STAR 结构说明项目：背景是求职资料分散且匹配效率低；任务是交付可登录、可上传简历、可做岗位分析和知识问答的系统；行动包括 FastAPI API、MySQL 持久化、Chroma 检索、DeepSeek 调用与 Docker 编排；结果是形成可重复演示的完整业务闭环。",
            s["body"],
        ),
        Paragraph("四、常见面试问题", s["heading"]),
        Paragraph(
            "1. 如何保证不同用户的知识库向量互不泄露？<br/>"
            "2. 模型输出不符合 JSON 结构时如何处理？<br/>"
            "3. PDF 上传、解析、向量化失败时如何回滚？<br/>"
            "4. MySQL 与 Redis 在系统中分别承担什么职责？<br/>"
            "5. 如果首次加载 Embedding 模型很慢，演示前如何预热？",
            s["body"],
        ),
        Paragraph("五、建议准备的改进点", s["heading"]),
        Paragraph(
            "加分改进包括 Kubernetes 部署、CI/CD、Prometheus 指标、请求链路追踪、向量检索评测集和端到端浏览器测试。若当前尚未实现，应如实说明规划，不要把计划描述成已完成成果。",
            s["body"],
        ),
        Spacer(1, 8),
        Paragraph("演示问法：这个岗位最看重哪些能力？回答中应引用本文件名。", s["small"]),
    ]
    document(ROOT / "python-ai-interview-guide.pdf").build(
        story, onFirstPage=footer, onLaterPages=footer
    )


if __name__ == "__main__":
    build_resume()
    build_knowledge()
