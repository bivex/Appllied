"""Domain events for OCR system."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from .enums import OCRPath


class DomainEvent:
    """Base class for all domain events in the system."""

    def __init__(self):
        """Initialize domain event base state with event ID and creation timestamp."""
        self._event_id = uuid4()
        self._occurred_at = datetime.now(timezone.utc)

    @property
    def event_id(self) -> UUID:
        """Unique event ID."""
        return self._event_id

    @property
    def occurred_at(self) -> datetime:
        """Timestamp when the event occurred in UTC."""
        return self._occurred_at


class OCRRequested(DomainEvent):
    """Event emitted when an OCR processing request is initiated."""

    def __init__(self, image_url: str, document_id: UUID):
        """Initialize OCRRequested event with image URL and target document ID."""
        super().__init__()
        self.image_url = image_url
        self.document_id = document_id


class OCREngineSelected(DomainEvent):
    """Event emitted when an OCR processing path strategy is selected."""

    def __init__(self, document_id: UUID, path: OCRPath, reason: str):
        """Initialize OCREngineSelected event with document ID, execution path and decision rationale."""
        super().__init__()
        self.document_id = document_id
        self.path = path
        self.reason = reason


class TextDetected(DomainEvent):
    """Event emitted when text region detection finishes."""

    def __init__(self, document_id: UUID, regions: int):
        """Initialize TextDetected event with document ID and region count."""
        super().__init__()
        self.document_id = document_id
        self.regions = regions


class TextRecognized(DomainEvent):
    """Event emitted when text recognition finishes for all detected lines."""

    def __init__(self, document_id: UUID, lines: int, avg_confidence: float):
        """Initialize TextRecognized event with line count and average confidence score."""
        super().__init__()
        self.document_id = document_id
        self.lines = lines
        self.avg_confidence = avg_confidence


class LanguageCorrected(DomainEvent):
    """Event emitted when post-processing language correction is applied."""

    def __init__(self, document_id: UUID, corrections: int):
        """Initialize LanguageCorrected event with number of corrections applied."""
        super().__init__()
        self.document_id = document_id
        self.corrections = corrections


class DocumentStructured(DomainEvent):
    """Event emitted when paragraph and table structure extraction finishes."""

    def __init__(self, document_id: UUID, paragraphs: int, tables: int):
        """Initialize DocumentStructured event with paragraph and table counts."""
        super().__init__()
        self.document_id = document_id
        self.paragraphs = paragraphs
        self.tables = tables


class OCRCompleted(DomainEvent):
    """Event emitted when the complete document OCR pipeline finishes."""

    def __init__(self, document_id: UUID, processing_time_ms: int):
        """Initialize OCRCompleted event with total processing duration in milliseconds."""
        super().__init__()
        self.document_id = document_id
        self.processing_time_ms = processing_time_ms
