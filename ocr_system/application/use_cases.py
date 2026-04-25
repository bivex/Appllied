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
        # Create aggregate
        document = Document(image_url=image_url, document_type=document_type)
        aggregate = OCRAggregate(document)
        aggregate.record_event(OCRRequested(image_url, document.id))

        # Retrieve image
        image_data = await self.image_source.get_image(image_url)

        # Select processing path
        # In real implementation, we'd analyze image to estimate text density
        path = self.path_selector.select_path(
            image_size=(1, 1),  # placeholder, need actual dimensions
            estimated_text_density=self.ESTIMATED_TEXT_DENSITY_DEFAULT,
            language_hint=None,
        )

        aggregate.record_event(
            OCREngineSelected(document.id, path, "heuristic selection")
        )

        # Process with selected path
        ocr_result = await self.ocr_engine.recognize(image_data, path)

        # Build domain entities from result
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

        # Apply language correction if needed
        corrected_lines = []
        total_corrections = 0
        for line in document.lines:
            corrected_text, corrections = self.ocr_engine.correct_language(line.text)
            if corrected_text != line.text:
                line.text = corrected_text
                total_corrections += corrections
                corrected_lines.append(line)

        if total_corrections > 0:
            aggregate.record_event(LanguageCorrected(document.id, total_corrections))

        # Extract structure (paragraphs, tables, entities)
        structured_doc = self.ocr_engine.extract_structure(document)

        # Mark as processed
        document.mark_processed()
        aggregate.record_event(OCRCompleted(document.id, ocr_result.processing_time_ms))

        # Persist
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
        document._paragraphs.clear()
        document._tables.clear()

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
