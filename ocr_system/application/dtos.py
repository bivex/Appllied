"""Data Transfer Objects for application layer."""

from __future__ import annotations

from typing import List

from domain import BoundingBox, Paragraph, Table, Entity


class LineResult:
    """Result for a single text line."""

    def __init__(self, text: str, bounding_box: BoundingBox, confidence: float):
        self.text = text
        self.bounding_box = bounding_box
        self.confidence = confidence


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


class StructuredDocument:
    """Structured extraction result."""

    def __init__(
        self, paragraphs: List[Paragraph], tables: List[Table], entities: List[Entity]
    ):
        self.paragraphs = paragraphs
        self.tables = tables
        self.entities = entities
