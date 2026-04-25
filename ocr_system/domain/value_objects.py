"""Value objects for OCR domain."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass(frozen=True)
class BoundingBox:
    """Immutable bounding box representation."""

    x: float
    y: float
    width: float
    height: float
    confidence: float = 1.0

    def intersect(self, other: BoundingBox) -> Optional[BoundingBox]:
        x1 = max(self.x, other.x)
        y1 = max(self.y, other.y)
        x2 = min(self.x + self.width, other.x + other.width)
        y2 = min(self.y + self.height, other.y + other.height)
        if x2 <= x1 or y2 <= y1:
            return None
        return BoundingBox(
            x=x1,
            y=y1,
            width=x2 - x1,
            height=y2 - y1,
            confidence=min(self.confidence, other.confidence),
        )

    def iou(self, other: BoundingBox) -> float:
        intersection = self.intersect(other)
        if intersection is None:
            return 0.0
        union_area = self.area + other.area - intersection.area
        return intersection.area / union_area if union_area > 0 else 0.0

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def center(self) -> Tuple[float, float]:
        return (self.x + self.width / 2, self.y + self.height / 2)


@dataclass(frozen=True)
class Point:
    x: float
    y: float


@dataclass(frozen=True)
class Polygon:
    points: List[Point]

    def bounding_box(self) -> BoundingBox:
        if not self.points:
            raise ValueError("Polygon must have at least one point")
        xs = [p.x for p in self.points]
        ys = [p.y for p in self.points]
        return BoundingBox(
            x=min(xs), y=min(ys), width=max(xs) - min(xs), height=max(ys) - min(ys)
        )


@dataclass(frozen=True)
class TextRange:
    start: int
    end: int

    def length(self) -> int:
        return self.end - self.start


@dataclass(frozen=True)
class Language:
    code: str
    script: Optional[str] = None
    confidence: float = 1.0

    def __hash__(self) -> int:
        return hash((self.code, self.script))
