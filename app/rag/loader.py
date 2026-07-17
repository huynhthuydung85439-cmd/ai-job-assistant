from dataclasses import dataclass
from uuid import uuid4

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.services.pdf_parser import PDFParserService


@dataclass(frozen=True, slots=True)
class LoadedKnowledge:
    document_id: str
    filename: str
    pages: int
    chunks: list[Document]


class KnowledgeLoader:
    def __init__(
        self,
        pdf_parser: PDFParserService,
        chunk_size: int,
        chunk_overlap: int,
    ) -> None:
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        self._pdf_parser = pdf_parser
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            add_start_index=True,
            separators=["\n\n", "\n", "。", "！", "？", ". ", " ", ""],
        )

    def load_pdf(self, filename: str, content: bytes) -> LoadedKnowledge:
        parsed = self._pdf_parser.parse(filename=filename, content=content)
        document_id = str(uuid4())
        document = Document(
            page_content=parsed.text,
            metadata={
                "source": parsed.filename,
                "filename": parsed.filename,
                "pages": parsed.pages,
                "document_id": document_id,
            },
        )
        split_documents = self._splitter.split_documents([document])
        chunks = [
            Document(
                id=f"{document_id}:{index}",
                page_content=chunk.page_content,
                metadata={**chunk.metadata, "chunk_index": index},
            )
            for index, chunk in enumerate(split_documents)
        ]
        return LoadedKnowledge(
            document_id=document_id,
            filename=parsed.filename,
            pages=parsed.pages,
            chunks=chunks,
        )
