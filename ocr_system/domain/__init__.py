"""OCR System - Domain Layer

Core business logic, entities, value objects, aggregates, and domain events.
No dependencies on frameworks or infrastructure.
"""

from .enums import DocumentType, EntityType, OCRPath
from .events import (
    DomainEvent,
    OCRCompleted,
    OCRRequested,
    OCREngineSelected,
    TextDetected,
    TextRecognized,
    LanguageCorrected,
    DocumentStructured,
)
from .entities import (
    Character,
    Document,
    Entity,
    OCRAggregate,
    Paragraph,
    Table,
    TextLine,
    Word,
)
from .value_objects import (
    BoundingBox,
    Language,
    Point,
    Polygon,
    TextRange,
)

__all__ = [
    # Enums
    "DocumentType",
    "EntityType",
    "OCRPath",
    # Events
    "DomainEvent",
    "OCRCompleted",
    "OCRRequested",
    "OCREngineSelected",
    "TextDetected",
    "TextRecognized",
    "LanguageCorrected",
    "DocumentStructured",
    # Entities
    "Character",
    "Document",
    "Entity",
    "OCRAggregate",
    "Paragraph",
    "Table",
    "TextLine",
    "Word",
    # Value Objects
    "BoundingBox",
    "Language",
    "Point",
    "Polygon",
    "TextRange",
]
