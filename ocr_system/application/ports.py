"""Service and repository interfaces (Ports) for application layer."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional, Protocol
from uuid import UUID

from ocr_system.domain import Document, DocumentType
from .dtos import OCRResult, LineResult, StructuredDocument
from ocr_system.domain import BoundingBox, OCRPath, Language


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


class DocumentRepository(Protocol):
    """Repository interface for storing and retrieving documents."""

    async def save(self, document: Document) -> None:
        ...

    async def get_by_id(self, document_id: UUID) -> Optional[Document]:
        ...

    async def list_by_type(self, document_type: DocumentType) -> List[Document]:
        ...


class ImageSource(Protocol):
    """Port for retrieving images from various sources."""

    async def get_image(self, image_url: str) -> bytes:
        ...

    async def exists(self, image_url: str) -> bool:
        ...
