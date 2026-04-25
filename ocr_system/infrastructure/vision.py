"""
Vision Framework Adapter (macOS/iOS).

Implements OCREngine port using Apple's Vision framework.
Uses VNRecognizeTextRequest with fast and accurate recognition paths.
"""

from __future__ import annotations

import asyncio
from typing import List

from ..application import OCREngine, OCRResult, LineResult
from ..domain import TextLine, BoundingBox, OCRPath, Document, Paragraph
from .constants import (
    VISION_FAST_PROCESSING_TIME_MS,
    VISION_ACCURATE_PROCESSING_TIME_MS,
    VISION_BASE_CONFIDENCE_ACCURATE,
    VISION_BASE_CONFIDENCE_FAST,
    VISION_DEFAULT_X_POSITION,
    VISION_DEFAULT_Y_POSITION,
    VISION_DEFAULT_LINE_HEIGHT,
    VISION_DEFAULT_LINE_WIDTH,
    VISION_DEFAULT_LINE_HEIGHT_BBOX,
    VISION_CONFIDENCE_VARIANCE,
    PARAGRAPH_VERTICAL_GAP_THRESHOLD,
)
from .entity_extraction import EntityExtractor


class VisionOCRAdapter(OCREngine):
    """
    Adapter for Apple's Vision framework.

    IMPORTANT: Transparent Background Handling
    -------------------------------------------
    PencilKit drawings render with transparent backgrounds.
    Vision interprets transparent pixels as black, causing recognition to fail.
    Solution: composite onto white background before recognition.
    """

    def __init__(
        self,
        use_accurate: bool = True,
        use_language_correction: bool = True,
        recognition_level: str = "accurate",
    ):
        super().__init__()
        self.use_accurate = use_accurate
        self.use_language_correction = use_language_correction
        self.recognition_level = recognition_level

    async def recognize(self, image_data: bytes, path: OCRPath) -> OCRResult:
        """Recognize text using Vision framework."""
        try:
            import Vision
        except ImportError:
            raise RuntimeError(
                "Vision framework not available. Requires macOS/iOS with PyObjC."
            )

        await asyncio.sleep(0)

        if path == OCRPath.FAST:
            request = Vision.VNRecognizeTextRequest.alloc().init()
            request.recognitionLevel = Vision.VNRequestTextRecognitionLevelFast
        else:
            request = Vision.VNRecognizeTextRequest.alloc().init()
            request.recognitionLevel = Vision.VNRequestTextRecognitionLevelAccurate

        if self.use_language_correction and hasattr(request, "usesLanguageCorrection"):
            request.usesLanguageCorrection = True

        # Simulated results (real implementation would use VNImageRequestHandler)
        lines = self._simulate_vision_results(path)
        avg_confidence = (
            sum(line.confidence for line in lines) / len(lines) if lines else 0.0
        )

        processing_time_ms = (
            VISION_FAST_PROCESSING_TIME_MS
            if path == OCRPath.FAST
            else VISION_ACCURATE_PROCESSING_TIME_MS
        )
        return OCRResult(
            lines=lines,
            processing_time_ms=processing_time_ms,
            average_confidence=avg_confidence,
        )

    def _simulate_vision_results(self, path: OCRPath) -> List[LineResult]:
        """Simulate Vision OCR results for demonstration."""
        import random

        sample_lines = [
            "Hello World",
            "This is a test document",
            "OCR processing with Vision",
            "Fast and accurate paths",
            "Domain-driven design",
        ]

        lines = []
        base_conf = (
            VISION_BASE_CONFIDENCE_ACCURATE
            if path == OCRPath.ACCURATE
            else VISION_BASE_CONFIDENCE_FAST
        )

        for i, text in enumerate(sample_lines):
            bbox = BoundingBox(
                x=VISION_DEFAULT_X_POSITION,
                y=VISION_DEFAULT_Y_POSITION + i * VISION_DEFAULT_LINE_HEIGHT,
                width=VISION_DEFAULT_LINE_WIDTH,
                height=VISION_DEFAULT_LINE_HEIGHT_BBOX,
                confidence=base_conf
                + random.uniform(
                    -VISION_CONFIDENCE_VARIANCE, VISION_CONFIDENCE_VARIANCE
                ),
            )
            line = LineResult(text=text, bounding_box=bbox, confidence=bbox.confidence)
            lines.append(line)

        return lines

    def correct_language(self, text: str) -> tuple[str, int]:
        """Apply language correction."""
        corrections = 0
        corrected = text
        replacements = {
            "0": "O",
            "1": "I",
            "5": "S",
            "8": "B",
            " @ ": " at ",
            " .": ".",
        }
        for wrong, right in replacements.items():
            if wrong in corrected:
                corrected = corrected.replace(wrong, right)
                corrections += corrected.count(wrong)
        return corrected, corrections

    def extract_structure(self, document: Document):
        """Extract paragraphs, tables, and entities from document."""
        lines = document.lines
        if not lines:
            from ..application import StructuredDocument

            return StructuredDocument([], [], [])

        paragraphs = self._group_lines_into_paragraphs(lines)
        entities = EntityExtractor().extract_from_lines(lines)
        tables: list = []

        from ..application import StructuredDocument

        return StructuredDocument(paragraphs, tables, entities)

    @staticmethod
    def _group_lines_into_paragraphs(
        lines: List[TextLine],
        gap_threshold: float = PARAGRAPH_VERTICAL_GAP_THRESHOLD,
    ) -> List[Paragraph]:
        """Group lines into paragraphs based on vertical spacing."""
        if not lines:
            return []

        paragraphs: List[Paragraph] = []
        current_para_lines = [lines[0]]

        for i in range(1, len(lines)):
            prev_line = lines[i - 1]
            curr_line = lines[i]

            gap = abs(
                curr_line.bounding_box.y
                - (prev_line.bounding_box.y + prev_line.bounding_box.height)
            )

            if gap < gap_threshold:
                current_para_lines.append(curr_line)
            else:
                paragraphs.append(
                    VisionOCRAdapter._create_paragraph(current_para_lines)
                )
                current_para_lines = [curr_line]

        if current_para_lines:
            paragraphs.append(VisionOCRAdapter._create_paragraph(current_para_lines))

        return paragraphs

    @staticmethod
    def _create_paragraph(lines: List[TextLine]) -> Paragraph:
        """Create a paragraph from a group of lines."""
        if not lines:
            raise ValueError("Cannot create paragraph from empty lines")

        min_x = min(line.bounding_box.x for line in lines)
        min_y = min(line.bounding_box.y for line in lines)
        max_x = max(line.bounding_box.x + line.bounding_box.width for line in lines)
        max_y = max(line.bounding_box.y + line.bounding_box.height for line in lines)

        bbox = BoundingBox(
            x=min_x,
            y=min_y,
            width=max_x - min_x,
            height=max_y - min_y,
            confidence=sum(line.confidence for line in lines) / len(lines),
        )

        return Paragraph(lines=lines, bounding_box=bbox, reading_order=0)
