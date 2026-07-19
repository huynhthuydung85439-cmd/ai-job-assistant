from io import BytesIO

from reportlab.pdfgen import canvas

from app.rag.loader import KnowledgeLoader
from app.services.pdf_parser import PDFParserService


def create_knowledge_pdf() -> bytes:
    output = BytesIO()
    document = canvas.Canvas(output)
    text = document.beginText(72, 750)
    for index in range(12):
        text.textLine(
            f"Requirement {index}: Python FastAPI MySQL Redis Docker Kubernetes experience."
        )
    document.drawText(text)
    document.showPage()
    document.save()
    return output.getvalue()


def test_knowledge_loader_extracts_and_splits_pdf() -> None:
    loader = KnowledgeLoader(
        pdf_parser=PDFParserService(),
        chunk_size=180,
        chunk_overlap=30,
    )

    loaded = loader.load_pdf(
        "job-description.pdf",
        create_knowledge_pdf(),
        {"user_id": "42", "collection_name": "test_knowledge"},
    )

    assert loaded.filename == "job-description.pdf"
    assert loaded.pages == 1
    assert len(loaded.chunks) > 1
    assert all(chunk.id for chunk in loaded.chunks)
    assert all(chunk.metadata["source"] == "job-description.pdf" for chunk in loaded.chunks)
    assert all(chunk.metadata["user_id"] == "42" for chunk in loaded.chunks)
    assert [chunk.metadata["chunk_index"] for chunk in loaded.chunks] == list(
        range(len(loaded.chunks))
    )
