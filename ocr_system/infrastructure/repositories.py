"""
Repositories for Document persistence.

In-memory implementation for development and testing.
Database repositories (SQLAlchemy, PostgreSQL) can be added.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from uuid import UUID

from ..application import DocumentRepository
from ..domain import Document, DocumentType


class InMemoryDocumentRepository(DocumentRepository):
    """In-memory repository for documents."""

    def __init__(self):
        super().__init__()
        self._documents: Dict[UUID, Document] = {}

    async def save(self, document: Document) -> None:
        """Save document to memory."""
        self._documents[document.id] = document

    async def get_by_id(self, document_id: UUID) -> Optional[Document]:
        """Retrieve document by ID."""
        return self._documents.get(document_id)

    async def list_by_type(self, document_type: DocumentType) -> List[Document]:
        """List documents by type."""
        return [
            doc
            for doc in self._documents.values()
            if doc.document_type == document_type
        ]
