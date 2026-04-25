"""Domain entities for OCR system."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from .enums import DocumentType, EntityType
from .events import DomainEvent
from .value_objects import BoundingBox, Language


class Character:
    """A single character recognition result."""

    def __init__(self, text: str, bounding_box: BoundingBox, confidence: float):
        self._id = uuid4()
        self._text = text
        self._bounding_box = bounding_box
        self._confidence = confidence

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def text(self) -> str:
        return self._text

    @property
    def bounding_box(self) -> BoundingBox:
        return self._bounding_box

    @property
    def confidence(self) -> float:
        return self._confidence


class Word:
    """A word within recognized text."""

    def __init__(
        self,
        text: str,
        bounding_box: BoundingBox,
        confidence: float,
        characters: Optional[List[Character]] = None,
    ):
        self._id = uuid4()
        self._text = text
        self._bounding_box = bounding_box
        self._confidence = confidence
        self._characters: List[Character] = characters or []

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def text(self) -> str:
        return self._text

    @property
    def bounding_box(self) -> BoundingBox:
        return self._bounding_box

    @property
    def confidence(self) -> float:
        return self._confidence

    @property
    def characters(self) -> List[Character]:
        return self._characters.copy()

    def add_character(self, char: Character) -> None:
        self._characters.append(char)

    def split_into_characters(self) -> List[Character]:
        if self._characters:
            return self._characters

        chars = []
        char_width = self._bounding_box.width / len(self._text) if self._text else 0

        for i, char_text in enumerate(self._text):
            char = Character(
                text=char_text,
                bounding_box=BoundingBox(
                    x=self._bounding_box.x + i * char_width,
                    y=self._bounding_box.y,
                    width=char_width,
                    height=self._bounding_box.height,
                    confidence=self._confidence,
                ),
                confidence=self._confidence,
            )
            chars.append(char)

        self._characters = chars
        return chars


class TextLine:
    """A line of recognized text with bounding box."""

    def __init__(
        self,
        text: str,
        bounding_box: BoundingBox,
        confidence: float,
        words: Optional[List[Word]] = None,
    ):
        self._id = uuid4()
        self._text = text
        self._bounding_box = bounding_box
        self._confidence = confidence
        self._words: List[Word] = words or []
        self._language: Optional[Language] = None

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        self._text = value

    @property
    def bounding_box(self) -> BoundingBox:
        return self._bounding_box

    @bounding_box.setter
    def bounding_box(self, value: BoundingBox) -> None:
        self._bounding_box = value

    @property
    def confidence(self) -> float:
        return self._confidence

    @property
    def words(self) -> List[Word]:
        return self._words.copy()

    @property
    def language(self) -> Optional[Language]:
        return self._language

    @language.setter
    def language(self, value: Language) -> None:
        self._language = value

    def add_word(self, word: Word) -> None:
        self._words.append(word)

    def split_into_words(self) -> List[Word]:
        if self._words:
            return self._words

        words = []
        word_count = max(1, len(self._text.split()))
        word_width = self._bounding_box.width / word_count
        current_x = self._bounding_box.x

        for i, word_text in enumerate(self._text.split()):
            word = Word(
                text=word_text,
                bounding_box=BoundingBox(
                    x=current_x + i * word_width,
                    y=self._bounding_box.y,
                    width=word_width,
                    height=self._bounding_box.height,
                    confidence=self._confidence,
                ),
                confidence=self._confidence,
            )
            words.append(word)

        self._words = words
        return words


class Paragraph:
    """Structured paragraph grouping lines."""

    def __init__(
        self, lines: List[TextLine], bounding_box: BoundingBox, reading_order: int
    ):
        self._id = uuid4()
        self._lines = lines
        self._bounding_box = bounding_box
        self._reading_order = reading_order

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def lines(self) -> List[TextLine]:
        return self._lines.copy()

    @property
    def text(self) -> str:
        return " ".join(line.text for line in self._lines)

    @property
    def bounding_box(self) -> BoundingBox:
        return self._bounding_box

    @property
    def reading_order(self) -> int:
        return self._reading_order


class Table:
    """Detected table structure."""

    def __init__(
        self, rows: List[List[TextLine]], bounding_box: BoundingBox, columns: int
    ):
        self._id = uuid4()
        self._rows = rows
        self._bounding_box = bounding_box
        self._columns = columns

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def rows(self) -> List[List[TextLine]]:
        return self._rows.copy()

    @property
    def bounding_box(self) -> BoundingBox:
        return self._bounding_box

    @property
    def columns(self) -> int:
        return self._columns

    def to_markdown(self) -> str:
        lines = []
        for row in self._rows:
            lines.append("| " + " | ".join(cell.text for cell in row) + " |")
        return "\n".join(lines)


class Entity:
    """Extracted structured entity."""

    def __init__(
        self,
        entity_type: EntityType,
        value: str,
        bounding_box: BoundingBox,
        confidence: float,
    ):
        self._id = uuid4()
        self._entity_type = entity_type
        self._value = value
        self._bounding_box = bounding_box
        self._confidence = confidence

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def entity_type(self) -> EntityType:
        return self._entity_type

    @property
    def value(self) -> str:
        return self._value

    @property
    def bounding_box(self) -> BoundingBox:
        return self._bounding_box

    @property
    def confidence(self) -> float:
        return self._confidence


class DocumentBase:
    """Base class with core document properties and line management."""

    def __init__(
        self,
        image_url: str,
        document_type: DocumentType,
        lines: Optional[List[TextLine]] = None,
    ):
        self._id = uuid4()
        self._image_url = image_url
        self._document_type = document_type
        self._lines: List[TextLine] = lines or []
        self._created_at = datetime.now(timezone.utc)
        self._processed_at: Optional[datetime] = None

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def image_url(self) -> str:
        return self._image_url

    @property
    def document_type(self) -> DocumentType:
        return self._document_type

    @property
    def lines(self) -> List[TextLine]:
        return self._lines.copy()

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def processed_at(self) -> Optional[datetime]:
        return self._processed_at

    def add_line(self, line: TextLine) -> None:
        self._lines.append(line)

    def mark_processed(self) -> None:
        self._processed_at = datetime.now(timezone.utc)

    def get_full_text(self) -> str:
        return "\n".join(line.text for line in self._lines)


class Document(DocumentBase):
    """Aggregate root for a recognized document with structure management."""

    def __init__(
        self,
        image_url: str,
        document_type: DocumentType,
        lines: Optional[List[TextLine]] = None,
    ):
        super().__init__(image_url=image_url, document_type=document_type, lines=lines)
        self._paragraphs: List[Paragraph] = []
        self._tables: List[Table] = []
        self._metadata: Dict[str, Any] = {}

    @property
    def paragraphs(self) -> List[Paragraph]:
        return self._paragraphs.copy()

    @property
    def tables(self) -> List[Table]:
        return self._tables.copy()

    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata.copy()

    def add_paragraph(self, paragraph: Paragraph) -> None:
        self._paragraphs.append(paragraph)

    def add_table(self, table: Table) -> None:
        self._tables.append(table)

    def clear_structure(self) -> None:
        """Remove all paragraphs and tables from the document."""
        self._paragraphs.clear()
        self._tables.clear()

    def extract_entities(self) -> List[Entity]:
        entities = []
        for line in self._lines:
            # Delegate to domain service or engine
            pass
        return entities


class OCRAggregate:
    """Aggregate root for OCR processing lifecycle."""

    def __init__(self, document: Document):
        self._document = document
        self._domain_events: List[DomainEvent] = []

    @property
    def document(self) -> Document:
        return self._document

    @property
    def domain_events(self) -> List[DomainEvent]:
        return self._domain_events.copy()

    def record_event(self, event: DomainEvent) -> None:
        self._domain_events.append(event)

    def clear_events(self) -> None:
        self._domain_events.clear()
