"""Domain enums for OCR system."""

from enum import Enum


class DocumentType(Enum):
    """Classification of document types processed by OCR engine."""

    GENERIC = "generic"
    FORM = "form"
    INVOICE = "invoice"
    RECEIPT = "receipt"
    BUSINESS_CARD = "business_card"
    HANDWRITTEN = "handwritten"
    TABLE = "table"
    ID_DOCUMENT = "id_document"


class OCRPath(Enum):
    """Processing execution mode selection (fast vs accurate)."""

    FAST = "fast"
    ACCURATE = "accurate"


class EntityType(Enum):
    """Structured entity types extracted from recognized text."""

    EMAIL = "email"
    PHONE = "phone"
    URL = "url"
    DATE = "date"
    ADDRESS = "address"
    NAME = "name"
    ORGANIZATION = "organization"
