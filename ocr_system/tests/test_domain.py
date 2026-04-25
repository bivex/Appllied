"""
Unit tests for the OCR system domain layer.
"""

import datetime

import pytest
from ocr_system.domain import (
    BoundingBox,
    Point,
    Polygon,
    Language,
    Character,
    Word,
    TextLine,
    Document,
    Paragraph,
    Table,
    DocumentType,
    OCRPath,
    DomainEvent,
    OCRRequested,
    OCREngineSelected,
    TextRecognized,
    LanguageCorrected,
    OCRCompleted,
    OCRAggregate,
)

# Test constants — named for clarity
CONF_HIGH = 0.95
CONF_ABOVE = 0.9
CONF_MID = 0.88
CONF_BELOW = 0.85
CONF_LOWER = 0.8

BBOX_SMALL_SIZE = 10
BBOX_MEDIUM_WIDTH = 20
BBOX_MEDIUM_HEIGHT = 10
BBOX_LARGE_WIDTH = 50
BBOX_LINE_WIDTH = 100
BBOX_LINE_HEIGHT = 20
BBOX_PARAGRAPH_WIDTH = 100
BBOX_PARAGRAPH_HEIGHT = 50
BBOX_DISJOINT_OFFSET = 20
BBOX_CENTER_HALF = 5.0
OCR_PROCESSING_TIME_MS = 150
LINE_Y_OFFSET = 20


class TestBoundingBox:
    def test_intersect(self):
        a = BoundingBox(0, 0, BBOX_SMALL_SIZE, BBOX_SMALL_SIZE, CONF_ABOVE)
        b = BoundingBox(5, 5, BBOX_SMALL_SIZE, BBOX_SMALL_SIZE, CONF_LOWER)
        inter = a.intersect(b)
        assert inter is not None
        assert inter.x == 5
        assert inter.y == 5
        assert inter.width == 5
        assert inter.height == 5
        assert inter.confidence == min(a.confidence, b.confidence)

    def test_intersect_none(self):
        a = BoundingBox(0, 0, BBOX_SMALL_SIZE, BBOX_SMALL_SIZE)
        b = BoundingBox(BBOX_DISJOINT_OFFSET, BBOX_DISJOINT_OFFSET, BBOX_SMALL_SIZE, BBOX_SMALL_SIZE)
        assert a.intersect(b) is None

    def test_iou(self):
        a = BoundingBox(0, 0, BBOX_SMALL_SIZE, BBOX_SMALL_SIZE)
        b = BoundingBox(0, 0, BBOX_SMALL_SIZE, BBOX_SMALL_SIZE)
        assert a.iou(b) == 1.0
        c = BoundingBox(BBOX_DISJOINT_OFFSET, BBOX_DISJOINT_OFFSET, BBOX_SMALL_SIZE, BBOX_SMALL_SIZE)
        assert a.iou(c) == 0.0

    def test_area(self):
        b = BoundingBox(1, 2, 3, 4)
        assert b.area == 12

    def test_center(self):
        b = BoundingBox(0, 0, BBOX_SMALL_SIZE, BBOX_SMALL_SIZE)
        assert b.center == (BBOX_CENTER_HALF, BBOX_CENTER_HALF)


class TestPolygon:
    def test_bounding_box(self):
        points = [Point(0, 0), Point(BBOX_SMALL_SIZE, 0), Point(BBOX_SMALL_SIZE, 5), Point(0, 5)]
        poly = Polygon(points)
        bbox = poly.bounding_box()
        assert bbox.x == 0
        assert bbox.y == 0
        assert bbox.width == BBOX_SMALL_SIZE
        assert bbox.height == 5


class TestLanguage:
    def test_hash(self):
        l1 = Language("en")
        l2 = Language("en")
        assert hash(l1) == hash(l2)
        l3 = Language("en", "Latn")
        assert hash(l1) != hash(l3)


class TestCharacter:
    def test_creation(self):
        char = Character("A", BoundingBox(0, 0, 1, 1), CONF_HIGH)
        assert char.text == "A"
        assert char.confidence == pytest.approx(CONF_HIGH)


class TestWord:
    def test_split_into_characters(self):
        word = Word("Hi", BoundingBox(0, 0, BBOX_MEDIUM_WIDTH, BBOX_MEDIUM_HEIGHT), CONF_ABOVE)
        chars = word.split_into_characters()
        assert len(chars) == 2
        assert chars[0].text == "H"
        assert chars[1].text == "i"
        assert word.characters == chars
        assert word.characters is not chars


class TestTextLine:
    def test_split_into_words(self):
        line = TextLine("Hello World", BoundingBox(0, 0, BBOX_LINE_WIDTH, BBOX_LINE_HEIGHT), CONF_BELOW)
        words = line.split_into_words()
        assert len(words) == 2
        assert words[0].text == "Hello"
        assert words[1].text == "World"

    def test_add_word(self):
        line = TextLine("Test", BoundingBox(0, 0, BBOX_LARGE_WIDTH, BBOX_MEDIUM_HEIGHT), CONF_ABOVE)
        word = Word("Test", BoundingBox(0, 0, BBOX_LARGE_WIDTH, BBOX_MEDIUM_HEIGHT), CONF_ABOVE)
        line.add_word(word)
        assert len(line.words) == 1
        assert line.words[0] is word

    def test_language_property(self):
        line = TextLine("Bonjour", BoundingBox(0, 0, BBOX_LARGE_WIDTH, BBOX_MEDIUM_HEIGHT), CONF_ABOVE)
        lang = Language("fr")
        line.language = lang
        assert line.language == lang


class TestDocument:
    def test_add_line(self):
        doc = Document("img.png", DocumentType.GENERIC)
        line = TextLine("Hello", BoundingBox(0, 0, BBOX_SMALL_SIZE, BBOX_SMALL_SIZE), CONF_ABOVE)
        doc.add_line(line)
        assert len(doc.lines) == 1

    def test_add_paragraph(self):
        doc = Document("img.png", DocumentType.GENERIC)
        para = Paragraph(
            lines=[], bounding_box=BoundingBox(0, 0, BBOX_PARAGRAPH_WIDTH, BBOX_PARAGRAPH_HEIGHT),
            reading_order=1,
        )
        doc.add_paragraph(para)
        assert len(doc.paragraphs) == 1

    def test_add_table(self):
        doc = Document("img.png", DocumentType.GENERIC)
        table = Table(
            rows=[[TextLine("Cell", BoundingBox(0, 0, BBOX_SMALL_SIZE, BBOX_SMALL_SIZE), CONF_ABOVE)]],
            bounding_box=BoundingBox(0, 0, BBOX_PARAGRAPH_WIDTH, BBOX_PARAGRAPH_WIDTH),
            columns=1,
        )
        doc.add_table(table)
        assert len(doc.tables) == 1

    def test_get_full_text(self):
        doc = Document("img.png", DocumentType.GENERIC)
        line1 = TextLine("Line1", BoundingBox(0, 0, BBOX_SMALL_SIZE, BBOX_SMALL_SIZE), CONF_ABOVE)
        line2 = TextLine("Line2", BoundingBox(0, LINE_Y_OFFSET, BBOX_SMALL_SIZE, BBOX_SMALL_SIZE), CONF_ABOVE)
        doc.add_line(line1)
        doc.add_line(line2)
        assert doc.get_full_text() == "Line1\nLine2"

    def test_mark_processed(self):
        doc = Document("img.png", DocumentType.GENERIC)
        before = datetime.datetime.now(datetime.timezone.utc)
        doc.mark_processed()
        after = datetime.datetime.now(datetime.timezone.utc)
        assert doc.processed_at is not None
        assert before <= doc.processed_at <= after


class TestOCRAggregate:
    def test_record_events(self):
        doc = Document("img.png", DocumentType.GENERIC)
        agg = OCRAggregate(doc)
        event = OCRRequested("img.png", doc.id)
        agg.record_event(event)
        assert len(agg.domain_events) == 1
        assert agg.domain_events[0] is event

    def test_clear_events(self):
        doc = Document("img.png", DocumentType.GENERIC)
        agg = OCRAggregate(doc)
        agg.record_event(OCRRequested("img.png", doc.id))
        agg.clear_events()
        assert len(agg.domain_events) == 0


class TestDomainEvents:
    def test_event_types(self):
        doc = Document("img.png", DocumentType.GENERIC)
        e1 = OCRRequested("img.png", doc.id)
        assert e1.document_id == doc.id

        e2 = OCREngineSelected(doc.id, OCRPath.FAST, "small image")
        assert e2.path == OCRPath.FAST

        e3 = TextRecognized(doc.id, 10, CONF_MID)
        assert e3.lines == 10

        e4 = LanguageCorrected(doc.id, 5)
        assert e4.corrections == 5

        e5 = OCRCompleted(doc.id, OCR_PROCESSING_TIME_MS)
        assert e5.processing_time_ms == 150
