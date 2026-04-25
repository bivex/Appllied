"""OCR System - Application Layer

Use cases, orchestrators, and domain services.
Coordinates the workflow without containing business logic.
"""

from .ports import DocumentRepository, ImageSource, OCREngine
from .dtos import LineResult, OCRResult, StructuredDocument
from .services import (
    LanguageCorrectionService,
    PathSelectionStrategy,
    SimplePathSelectionStrategy,
)
from .use_cases import (
    ProcessDocumentUseCase,
    ExtractStructureUseCase,
    GetDocumentUseCase,
    SearchDocumentsUseCase,
)

__all__ = [
    # Ports
    "DocumentRepository",
    "ImageSource",
    "OCREngine",
    # DTOs
    "LineResult",
    "OCRResult",
    "StructuredDocument",
    # Services
    "LanguageCorrectionService",
    "PathSelectionStrategy",
    "SimplePathSelectionStrategy",
    # Use Cases
    "ProcessDocumentUseCase",
    "ExtractStructureUseCase",
    "GetDocumentUseCase",
    "SearchDocumentsUseCase",
]
