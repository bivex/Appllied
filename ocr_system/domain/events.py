"""Domain events for OCR system."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from .enums import OCRPath


class DomainEvent:
    def __init__(self):
        self._event_id = uuid4()
        self._occurred_at = datetime.now(timezone.utc)

    @property
    def event_id(self) -> UUID:
        return self._event_id

    @property
    def occurred_at(self) -> datetime:
        return self._occurred_at


class OCRRequested(DomainEvent):
    def __init__(self, image_url: str, document_id: UUID):
        super().__init__()
        self.image_url = image_url
        self.document_id = document_id


class OCREngineSelected(DomainEvent):
    def __init__(self, document_id: UUID, path: OCRPath, reason: str):
        super().__init__()
        self.document_id = document_id
        self.path = path
        self.reason = reason


class TextDetected(DomainEvent):
    def __init__(self, document_id: UUID, regions: int):
        super().__init__()
        self.document_id = document_id
        self.regions = regions


class TextRecognized(DomainEvent):
    def __init__(self, document_id: UUID, lines: int, avg_confidence: float):
        super().__init__()
        self.document_id = document_id
        self.lines = lines
        self.avg_confidence = avg_confidence


class LanguageCorrected(DomainEvent):
    def __init__(self, document_id: UUID, corrections: int):
        super().__init__()
        self.document_id = document_id
        self.corrections = corrections


class DocumentStructured(DomainEvent):
    def __init__(self, document_id: UUID, paragraphs: int, tables: int):
        super().__init__()
        self.document_id = document_id
        self.paragraphs = paragraphs
        self.tables = tables


class OCRCompleted(DomainEvent):
    def __init__(self, document_id: UUID, processing_time_ms: int):
        super().__init__()
        self.document_id = document_id
        self.processing_time_ms = processing_time_ms
