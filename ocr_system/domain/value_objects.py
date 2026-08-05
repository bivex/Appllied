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

    @property
    def right(self) -> float:
        """Right coordinate of the bounding box."""
        return self.x + self.width

    @property
    def bottom(self) -> float:
        """Bottom coordinate of the bounding box."""
        return self.y + self.height

    def intersect(self, other: BoundingBox) -> Optional[BoundingBox]:
        """Calculate intersection rectangle with another bounding box."""
        x1 = max(self.x, other.x)
        y1 = max(self.y, other.y)
        x2 = min(self.right, other.right)
        y2 = min(self.bottom, other.bottom)
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
        """Calculate Intersection over Union (IoU) metric with another bounding box."""
        intersection = self.intersect(other)
        if intersection is None:
            return 0.0
        union_area = self.area + other.area - intersection.area
        return intersection.area / union_area if union_area > 0 else 0.0

    @property
    def area(self) -> float:
        """Area of the bounding box."""
        return self.width * self.height

    @property
    def center(self) -> Tuple[float, float]:
        """(x, y) center point of the bounding box."""
        return (self.x + self.width / 2, self.y + self.height / 2)


@dataclass(frozen=True)
class Point:
    """2D Point representation in normalized or pixel space."""

    x: float
    y: float


@dataclass(frozen=True)
class Polygon:
    """Multi-point polygon bounding region."""

    points: List[Point]

    def bounding_box(self) -> BoundingBox:
        """Compute axis-aligned bounding box enclosing all polygon points."""
        if not self.points:
            raise ValueError("Polygon must have at least one point")
        xs = [p.x for p in self.points]
        ys = [p.y for p in self.points]
        return BoundingBox(
            x=min(xs), y=min(ys), width=max(xs) - min(xs), height=max(ys) - min(ys)
        )


@dataclass(frozen=True)
class TextRange:
    """Character offset range within text string."""

    start: int
    end: int

    def length(self) -> int:
        """Length of the text range."""
        return self.end - self.start


@dataclass(frozen=True)
class Language:
    """Language metadata and confidence."""

    code: str
    script: Optional[str] = None
    confidence: float = 1.0

    def __hash__(self) -> int:
        """Compute hash code for language instance."""
        return hash((self.code, self.script))
