"""Domain enums for OCR system."""

from enum import Enum


class DocumentType(Enum):
    GENERIC = "generic"
    FORM = "form"
    INVOICE = "invoice"
    RECEIPT = "receipt"
    BUSINESS_CARD = "business_card"
    HANDWRITTEN = "handwritten"
    TABLE = "table"
    ID_DOCUMENT = "id_document"


class OCRPath(Enum):
    FAST = "fast"
    ACCURATE = "accurate"


class EntityType(Enum):
    EMAIL = "email"
    PHONE = "phone"
    URL = "url"
    DATE = "date"
    ADDRESS = "address"
    NAME = "name"
    ORGANIZATION = "organization"
