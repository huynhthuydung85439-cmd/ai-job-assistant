from io import BytesIO

import pytest
from reportlab.pdfgen import canvas

from app.core.exceptions import PDFParsingError
from app.services.pdf_parser import PDFParserService


def create_pdf(page_texts: list[str]) -> bytes:
    output = BytesIO()
    document = canvas.Canvas(output)
    for text in page_texts:
        document.drawString(72, 750, text)
        document.showPage()
    document.save()
    return output.getvalue()


def test_pdf_parser_extracts_text_and_page_count() -> None:
    parser = PDFParserService()

    result = parser.parse(
        filename="resume.pdf",
        content=create_pdf(["Python FastAPI experience", "MySQL and Redis projects"]),
    )

    assert result.filename == "resume.pdf"
    assert result.pages == 2
    assert "Python FastAPI experience" in result.text
    assert "MySQL and Redis projects" in result.text


def test_pdf_parser_rejects_invalid_pdf() -> None:
    with pytest.raises(PDFParsingError):
        PDFParserService().parse(filename="resume.pdf", content=b"not a pdf")


def test_pdf_parser_rejects_pdf_without_extractable_text() -> None:
    output = BytesIO()
    document = canvas.Canvas(output)
    document.showPage()
    document.save()

    with pytest.raises(PDFParsingError):
        PDFParserService().parse(filename="blank.pdf", content=output.getvalue())
