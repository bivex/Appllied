"""
Entity extraction from OCR text lines.

Extracts structured entities (emails, URLs, phone numbers) from
recognized text using regex pattern matching with bounding-box
estimation.
"""

from __future__ import annotations

import re
from typing import List, Tuple

from domain import (
    TextLine,
    BoundingBox,
    Entity,
    EntityType,
)


# Each entry is (compiled regex, entity type).
_ENTITY_PATTERNS: List[Tuple[re.Pattern[str], EntityType]] = [
    (re.compile(r"[\w\.-]+@[\w\.-]+\.\w+"), EntityType.EMAIL),
    (re.compile(r"https?://[^\s]+"), EntityType.URL),
    (re.compile(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"), EntityType.PHONE),
]


class EntityExtractor:
    """Extracts entities (emails, URLs, phone numbers) from text lines."""

    def extract_from_line(self, line: TextLine) -> List[Entity]:
        """Extract all recognised entities from a single text line."""
        entities: List[Entity] = []
        for pattern, entity_type in _ENTITY_PATTERNS:
            entities.extend(self._find_entities_by_pattern(line, pattern, entity_type))
        return entities

    def extract_from_lines(self, lines: List[TextLine]) -> List[Entity]:
        """Extract entities from every line in *lines*."""
        entities: List[Entity] = []
        for line in lines:
            entities.extend(self.extract_from_line(line))
        return entities

    @staticmethod
    def _find_entities_by_pattern(
        line: TextLine,
        pattern: re.Pattern[str],
        entity_type: EntityType,
    ) -> List[Entity]:
        """Find all matches of *pattern* in *line* and return Entity objects."""
        text = line.text
        text_len = len(text)
        if text_len == 0:
            return []

        entities: List[Entity] = []
        line_bbox = line.bounding_box

        for match in pattern.finditer(text):
            start, end = match.span()
            entity_text = text[start:end]

            # Estimate bounding box proportional to character positions.
            char_width = line_bbox.width / text_len
            bbox = BoundingBox(
                x=line_bbox.x + start * char_width,
                y=line_bbox.y,
                width=(end - start) * char_width,
                height=line_bbox.height,
                confidence=line.confidence,
            )
            entities.append(
                Entity(
                    entity_type=entity_type,
                    value=entity_text,
                    bounding_box=bbox,
                    confidence=line.confidence,
                )
            )

        return entities
