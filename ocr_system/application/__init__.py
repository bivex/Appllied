"""
OCR System - Application Layer

Use cases, orchestrators, and domain services.
Coordinates the workflow without containing business logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional, Protocol
from datetime import datetime
from uuid import UUID

from domain import (
    Document,
    DocumentType,
    TextLine,
    BoundingBox,
    OCRPath,
    Language,
    DomainEvent,
    OCRAggregate,
    Paragraph,
    Table,
    Entity,
    EntityType,
    OCRRequested,
    OCREngineSelected,
    TextDetected,
    TextRecognized,
    LanguageCorrected,
    DocumentStructured,
    OCRCompleted,
)


# ===============================
# Service Interfaces (Ports)
# ===============================


class OCREngine(ABC):
    """Port for OCR engine abstraction (Vision or custom)."""

    @abstractmethod
    async def recognize(self, image_data: bytes, path: OCRPath) -> OCRResult:
        """Recognize text from image using specified path."""
        ...

    @abstractmethod
    def correct_language(self, text: str) -> tuple[str, int]:
        """Apply language correction to text."""
        ...

    @abstractmethod
    def extract_structure(self, document: Document) -> StructuredDocument:
        """Extract paragraphs, tables, and entities."""
        ...


class OCRResult:
    """Result from OCR engine processing."""

    def __init__(
        self,
        lines: List[LineResult],
        processing_time_ms: int,
        average_confidence: float,
    ):
        self.lines = lines
        self.processing_time_ms = processing_time_ms
        self.average_confidence = average_confidence


class LineResult:
    """Result for a single text line."""

    def __init__(self, text: str, bounding_box: BoundingBox, confidence: float):
        self.text = text
        self.bounding_box = bounding_box
        self.confidence = confidence


class StructuredDocument:
    """Structured extraction result."""

    def __init__(
        self, paragraphs: List[Paragraph], tables: List[Table], entities: List[Entity]
    ):
        self.paragraphs = paragraphs
        self.tables = tables
        self.entities = entities


# ===============================
# Repository Interfaces (Ports)
# ===============================


class DocumentRepository(Protocol):
    """Repository interface for storing and retrieving documents."""

    async def save(self, document: Document) -> None: ...

    async def get_by_id(self, document_id: UUID) -> Optional[Document]: ...

    async def list_by_type(self, document_type: DocumentType) -> List[Document]: ...


class ImageSource(Protocol):
    """Port for retrieving images from various sources."""

    async def get_image(self, image_url: str) -> bytes: ...

    async def exists(self, image_url: str) -> bool: ...


# ===============================
# Domain Services
# ===============================


class LanguageCorrectionService:
    """Domain service for correcting OCR text based on language rules."""

    def __init__(self, language: Language):
        self.language = language

    def correct(self, text: str) -> tuple[str, int]:
        """
        Apply language-specific corrections.
        Returns corrected text and number of corrections made.
        """
        corrections = 0
        corrected = text

        # Common OCR errors and their corrections based on language
        # This is a simplified example - real implementation would use dictionaries
        common_errors = {
            "0": "O",  # zero -> capital O
            "1": "I",  # one -> capital I
            "5": "S",  # five -> capital S
            "8": "B",  # eight -> capital B
        }

        for error, correction in common_errors.items():
            if error in corrected:
                corrected = corrected.replace(error, correction)
                corrections += corrected.count(error)

        return corrected, corrections


class PathSelectionStrategy(ABC):
    """Strategy for selecting OCR processing path."""

    @abstractmethod
    def select_path(
        self,
        image_size: tuple[int, int],
        estimated_text_density: float,
        language_hint: Optional[Language],
    ) -> OCRPath: ...

    def estimate_processing_time(
        self, path: OCRPath, image_size: tuple[int, int]
    ) -> float:
        """Estimate processing time in milliseconds."""
        width, height = image_size
        pixels = width * height

        if path == OCRPath.FAST:
            return pixels / 1_000_000 * 10  # 10ms per megapixel
        else:
            return pixels / 1_000_000 * 100  # 100ms per megapixel


class SimplePathSelectionStrategy(PathSelectionStrategy):
    """Simple heuristic-based path selection."""

    def select_path(
        self,
        image_size: tuple[int, int],
        estimated_text_density: float,
        language_hint: Optional[Language],
    ) -> OCRPath:
        """Select FAST or ACCURATE based on image characteristics."""
        width, height = image_size
        megapixels = (width * height) / 1_000_000

        # Use fast path for small images or high text density
        if megapixels < 2.0 or estimated_text_density > 0.3:
            return OCRPath.FAST

        # Use accurate path for larger images with sparse text
        return OCRPath.ACCURATE


# ===============================
# Use Cases (Application Services)
# ===============================


class ProcessDocumentUseCase:
    """Use case for processing a document image with OCR."""

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
            estimated_text_density=0.1,
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
