"""Use Cases (Application Services) for OCR system."""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from domain import (
    Document,
    DocumentType,
    TextLine,
    OCRPath,
    DomainEvent,
    OCRAggregate,
    OCRRequested,
    OCREngineSelected,
    TextRecognized,
    LanguageCorrected,
    OCRCompleted,
)
from .ports import DocumentRepository, ImageSource, OCREngine
from .services import PathSelectionStrategy
from .dtos import StructuredDocument


class ProcessDocumentUseCase:
    """Use case for processing a document image with OCR."""

    # Constants for process document use case
    ESTIMATED_TEXT_DENSITY_DEFAULT = 0.1

    def __init__(
        self,
        image_source: ImageSource,
        ocr_engine: OCREngine,
        document_repository: DocumentRepository,
        path_selector: PathSelectionStrategy,
    ):
        self.image_source = image_source
        self.ocr_engine = ocr_engine
        self.document_repository = document_repository
        self.path_selector = path_selector

    async def execute(self, image_url: str, document_type: DocumentType) -> Document:
        """Execute OCR processing on a document image."""
        document = Document(image_url=image_url, document_type=document_type)
        aggregate = OCRAggregate(document)
        aggregate.record_event(OCRRequested(image_url, document.id))

        image_data = await self._retrieve_image(image_url, aggregate, document)

        path = self.path_selector.select_path(
            image_size=(1, 1),  # placeholder, need actual dimensions
            estimated_text_density=self.ESTIMATED_TEXT_DENSITY_DEFAULT,
            language_hint=None,
        )
        aggregate.record_event(
            OCREngineSelected(document.id, path, "heuristic selection")
        )

        ocr_result = await self._perform_ocr(image_data, path, aggregate, document)
        await self._apply_corrections(aggregate, document)
        return await self._finalize(aggregate, document, ocr_result)

    async def _retrieve_image(
        self, image_url: str, aggregate: OCRAggregate, document: Document
    ) -> bytes:
        """Retrieve image data from the source."""
        return await self.image_source.get_image(image_url)

    async def _perform_ocr(
        self, image_data: bytes, path: OCRPath, aggregate: OCRAggregate, document: Document
    ):
        """Run OCR recognition and build domain entities from results."""
        ocr_result = await self.ocr_engine.recognize(image_data, path)

        for line_data in ocr_result.lines:
            line = TextLine(
                text=line_data.text,
                bounding_box=line_data.bounding_box,
                confidence=line_data.confidence,
            )
            document.add_line(line)

        aggregate.record_event(
            TextRecognized(
                document.id, len(ocr_result.lines), ocr_result.average_confidence
            )
        )
        return ocr_result

    async def _apply_corrections(
        self, aggregate: OCRAggregate, document: Document
    ) -> None:
        """Apply language correction to recognized text lines."""
        total_corrections = 0
        for line in document.lines:
            corrected_text, corrections = self.ocr_engine.correct_language(line.text)
            if corrected_text != line.text:
                line.text = corrected_text
                total_corrections += corrections

        if total_corrections > 0:
            aggregate.record_event(LanguageCorrected(document.id, total_corrections))

    async def _finalize(
        self, aggregate: OCRAggregate, document: Document, ocr_result
    ) -> Document:
        """Extract structure, mark processed, and persist the document."""
        self.ocr_engine.extract_structure(document)

        document.mark_processed()
        aggregate.record_event(OCRCompleted(document.id, ocr_result.processing_time_ms))

        await self.document_repository.save(document)
        return document


class ExtractStructureUseCase:
    """Use case for extracting structured elements from OCR text."""

    def __init__(self, ocr_engine: OCREngine):
        self.ocr_engine = ocr_engine

    async def execute(self, document: Document) -> Document:
        """Extract paragraphs, tables, and entities from document."""
        structured = self.ocr_engine.extract_structure(document)

        # Clear previous structure
        document.clear_structure()

        for para in structured.paragraphs:
            document.add_paragraph(para)

        for table in structured.tables:
            document.add_table(table)

        return document


class GetDocumentUseCase:
    """Use case for retrieving a document by ID."""

    def __init__(self, document_repository: DocumentRepository):
        self.document_repository = document_repository

    async def execute(self, document_id: UUID) -> Optional[Document]:
        """Retrieve a document by its ID."""
        return await self.document_repository.get_by_id(document_id)


class SearchDocumentsUseCase:
    """Use case for searching documents by type or content."""

    def __init__(self, document_repository: DocumentRepository):
        self.document_repository = document_repository

    async def execute(
        self, document_type: Optional[DocumentType] = None, query: Optional[str] = None
    ) -> List[Document]:
        """Search documents by type and/or content query."""
        if document_type:
            return await self.document_repository.list_by_type(document_type)

        # In real implementation, would use full-text search
        return []
