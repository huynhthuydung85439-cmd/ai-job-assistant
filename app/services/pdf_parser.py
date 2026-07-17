from dataclasses import dataclass
from functools import lru_cache
from io import BytesIO

import pdfplumber

from app.core.exceptions import PDFParsingError

MAX_PDF_SIZE_BYTES = 10 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class ParsedPDF:
    filename: str
    text: str
    pages: int


class PDFParserService:
    def parse(self, filename: str, content: bytes) -> ParsedPDF:
        if not content or not content.startswith(b"%PDF-"):
            raise PDFParsingError

        try:
            with pdfplumber.open(BytesIO(content)) as pdf:
                pages = len(pdf.pages)
                page_texts = [self._normalize_text(page.extract_text() or "") for page in pdf.pages]
        except Exception as exc:
            raise PDFParsingError from exc

        text = "\n\n".join(page_text for page_text in page_texts if page_text).strip()
        if pages == 0 or not text:
            raise PDFParsingError

        return ParsedPDF(filename=filename, text=text, pages=pages)

    @staticmethod
    def _normalize_text(text: str) -> str:
        lines = [line.strip() for line in text.splitlines()]
        return "\n".join(line for line in lines if line).strip()


@lru_cache
def get_pdf_parser_service() -> PDFParserService:
    return PDFParserService()
