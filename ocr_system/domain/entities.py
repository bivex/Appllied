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
        """Initialize character entity with text, bounding box and confidence score."""
        self._id = uuid4()
        self._text = text
        self._bounding_box = bounding_box
        self._confidence = confidence

    @property
    def id(self) -> UUID:
        """Unique identifier of the character entity."""
        return self._id

    @property
    def text(self) -> str:
        """Single character text content."""
        return self._text

    @property
    def bounding_box(self) -> BoundingBox:
        """Bounding box of the character."""
        return self._bounding_box

    @property
    def confidence(self) -> float:
        """Confidence score between 0.0 and 1.0."""
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
        """Initialize word entity with text, bounding box, confidence score and optional character list."""
        self._id = uuid4()
        self._text = text
        self._bounding_box = bounding_box
        self._confidence = confidence
        self._characters: List[Character] = characters or []

    @property
    def id(self) -> UUID:
        """Unique identifier of the word entity."""
        return self._id

    @property
    def text(self) -> str:
        """Word string content."""
        return self._text

    @property
    def bounding_box(self) -> BoundingBox:
        """Bounding box of the word."""
        return self._bounding_box

    @property
    def confidence(self) -> float:
        """Confidence score between 0.0 and 1.0."""
        return self._confidence

    @property
    def characters(self) -> List[Character]:
        """List of child character entities."""
        return self._characters.copy()

    def add_character(self, char: Character) -> None:
        """Add a child character entity to the word."""
        self._characters.append(char)

    def split_into_characters(self) -> List[Character]:
        """Split word text into constituent character entities with computed geometry."""
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
        """Initialize line entity with text, bounding box, confidence score and optional word list."""
        self._id = uuid4()
        self._text = text
        self._bounding_box = bounding_box
        self._confidence = confidence
        self._words: List[Word] = words or []
        self._language: Optional[Language] = None

    @property
    def id(self) -> UUID:
        """Unique identifier of the text line entity."""
        return self._id

    @property
    def text(self) -> str:
        """Line text content."""
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        """Update line text content."""
        self._text = value

    @property
    def bounding_box(self) -> BoundingBox:
        """Bounding box of the text line."""
        return self._bounding_box

    @bounding_box.setter
    def bounding_box(self, value: BoundingBox) -> None:
        """Update line bounding box."""
        self._bounding_box = value

    @property
    def confidence(self) -> float:
        """Confidence score between 0.0 and 1.0."""
        return self._confidence

    @property
    def words(self) -> List[Word]:
        """List of constituent word entities."""
        return self._words.copy()

    @property
    def language(self) -> Optional[Language]:
        """Detected or assigned language for the line."""
        return self._language

    @language.setter
    def language(self, value: Language) -> None:
        """Set detected language for the line."""
        self._language = value

    def add_word(self, word: Word) -> None:
        """Add a constituent word entity to the line."""
        self._words.append(word)

    def split_into_words(self) -> List[Word]:
        """Split text line into word entities with calculated bounding boxes."""
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
        """Initialize paragraph entity with constituent lines, enclosing box and reading order index."""
        self._id = uuid4()
        self._lines = lines
        self._bounding_box = bounding_box
        self._reading_order = reading_order

    @property
    def id(self) -> UUID:
        """Unique identifier of the paragraph entity."""
        return self._id

    @property
    def lines(self) -> List[TextLine]:
        """Constituent lines within the paragraph."""
        return self._lines.copy()

    @property
    def text(self) -> str:
        """Concatenated plain text of all paragraph lines."""
        return " ".join(line.text for line in self._lines)

    @property
    def bounding_box(self) -> BoundingBox:
        """Enclosing bounding box of the paragraph."""
        return self._bounding_box

    @property
    def reading_order(self) -> int:
        """Reading order sequence number."""
        return self._reading_order


class Table:
    """Detected table structure."""

    def __init__(
        self, rows: List[List[TextLine]], bounding_box: BoundingBox, columns: int
    ):
        """Initialize table entity with cell rows, bounding box and column count."""
        self._id = uuid4()
        self._rows = rows
        self._bounding_box = bounding_box
        self._columns = columns

    @property
    def id(self) -> UUID:
        """Unique identifier of the table entity."""
        return self._id

    @property
    def rows(self) -> List[List[TextLine]]:
        """List of table cell rows."""
        return self._rows.copy()

    @property
    def bounding_box(self) -> BoundingBox:
        """Bounding box enclosing the table."""
        return self._bounding_box

    @property
    def columns(self) -> int:
        """Number of columns in the table."""
        return self._columns

    def to_markdown(self) -> str:
        """Format table cell contents into Markdown table representation."""
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
        """Initialize extracted entity with type, value, bounding box and confidence score."""
        self._id = uuid4()
        self._entity_type = entity_type
        self._value = value
        self._bounding_box = bounding_box
        self._confidence = confidence

    @property
    def id(self) -> UUID:
        """Unique identifier of the entity."""
        return self._id

    @property
    def entity_type(self) -> EntityType:
        """Domain type classification of the entity."""
        return self._entity_type

    @property
    def value(self) -> str:
        """Extracted entity string value."""
        return self._value

    @property
    def bounding_box(self) -> BoundingBox:
        """Bounding box of the entity."""
        return self._bounding_box

    @property
    def confidence(self) -> float:
        """Extraction confidence score."""
        return self._confidence


class DocumentBase:
    """Base class with core document properties and line management."""

    def __init__(
        self,
        image_url: str,
        document_type: DocumentType,
        lines: Optional[List[TextLine]] = None,
    ):
        """Initialize document base state with image URL, document type and optional lines."""
        self._id = uuid4()
        self._image_url = image_url
        self._document_type = document_type
        self._lines: List[TextLine] = lines or []
        self._created_at = datetime.now(timezone.utc)
        self._processed_at: Optional[datetime] = None

    @property
    def id(self) -> UUID:
        """Unique document ID."""
        return self._id

    @property
    def image_url(self) -> str:
        """Source image location URI."""
        return self._image_url

    @property
    def document_type(self) -> DocumentType:
        """Document category classification."""
        return self._document_type

    @property
    def lines(self) -> List[TextLine]:
        """Recognized text lines in the document."""
        return self._lines.copy()

    @property
    def created_at(self) -> datetime:
        """Timestamp of document entity creation."""
        return self._created_at

    @property
    def processed_at(self) -> Optional[datetime]:
        """Timestamp when document processing completed."""
        return self._processed_at

    def add_line(self, line: TextLine) -> None:
        """Append a recognized text line to the document."""
        self._lines.append(line)

    def mark_processed(self) -> None:
        """Mark document as fully processed with current timestamp."""
        self._processed_at = datetime.now(timezone.utc)

    def get_full_text(self) -> str:
        """Get newline-delimited text of all document lines."""
        return "\n".join(line.text for line in self._lines)


class Document(DocumentBase):
    """Aggregate root for a recognized document with structure management."""

    def __init__(
        self,
        image_url: str,
        document_type: DocumentType,
        lines: Optional[List[TextLine]] = None,
    ):
        """Initialize Document aggregate root."""
        super().__init__(image_url=image_url, document_type=document_type, lines=lines)
        self._paragraphs: List[Paragraph] = []
        self._tables: List[Table] = []
        self._metadata: Dict[str, Any] = {}

    @property
    def paragraphs(self) -> List[Paragraph]:
        """Extracted paragraph structures."""
        return self._paragraphs.copy()

    @property
    def tables(self) -> List[Table]:
        """Extracted table structures."""
        return self._tables.copy()

    @property
    def metadata(self) -> Dict[str, Any]:
        """Arbitrary document metadata dictionary."""
        return self._metadata.copy()

    def add_paragraph(self, paragraph: Paragraph) -> None:
        """Add an extracted paragraph to the document structure."""
        self._paragraphs.append(paragraph)

    def add_table(self, table: Table) -> None:
        """Add an extracted table to the document structure."""
        self._tables.append(table)

    def clear_structure(self) -> None:
        """Remove all paragraphs and tables from the document."""
        self._paragraphs.clear()
        self._tables.clear()

    def extract_entities(self) -> List[Entity]:
        """Extract structured domain entities from document text lines."""
        entities = []
        for line in self._lines:
            pass
        return entities


class OCRAggregate:
    """Aggregate root for OCR processing lifecycle."""

    def __init__(self, document: Document):
        """Initialize OCR Aggregate with target document entity."""
        self._document = document
        self._domain_events: List[DomainEvent] = []

    @property
    def document(self) -> Document:
        """Target document aggregate root."""
        return self._document

    @property
    def domain_events(self) -> List[DomainEvent]:
        """Recorded domain events list."""
        return self._domain_events.copy()

    def record_event(self, event: DomainEvent) -> None:
        """Append a domain event to the internal event queue."""
        self._domain_events.append(event)

    def clear_events(self) -> None:
        """Clear all recorded domain events."""
        self._domain_events.clear()
