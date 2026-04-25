"""
OCR System - Infrastructure Layer

Adapters for external services: Vision framework, file system, databases.
Implements ports defined in application layer.
"""

from __future__ import annotations

import asyncio
import io
import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Dict, Any
from uuid import UUID

from application import (
    OCREngine,
    OCRResult,
    LineResult,
    StructuredDocument,
    DocumentRepository,
    ImageSource,
)
from domain import (
    Document,
    DocumentType,
    TextLine,
    BoundingBox,
    OCRPath,
    Language,
    Paragraph,
    Table,
    Entity,
    EntityType,
)
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
    CUSTOM_MODEL_MOCK_PROCESSING_TIME_MS,
    CUSTOM_MODEL_MOCK_CONFIDENCE_HIGH,
    CUSTOM_MODEL_MOCK_CONFIDENCE_MEDIUM,
    CUSTOM_MODEL_MOCK_CONFIDENCE_AVG,
    CUSTOM_MODEL_MOCK_X_POSITION,
    CUSTOM_MODEL_MOCK_Y_POSITION_LINE1,
    CUSTOM_MODEL_MOCK_Y_POSITION_LINE2,
    CUSTOM_MODEL_MOCK_LINE_WIDTH,
    CUSTOM_MODEL_MOCK_LINE_HEIGHT,
    CUSTOM_MODEL_MOCK_LINE2_WIDTH,
    HTTP_DEFAULT_TIMEOUT_SECONDS,
    HTTP_EXISTS_CHECK_TIMEOUT_SECONDS,
    OCR_DEFAULT_MAX_IMAGE_SIZE_MB,
)

# ===============================
# Vision Framework Adapter (macOS/iOS)
# ===============================


class VisionOCRAdapter(OCREngine):
    """
    Adapter for Apple's Vision framework.
    Uses VNRecognizeTextRequest with fast and accurate paths.

    IMPORTANT: Transparent Background Handling
    -------------------------------------------
    PencilKit drawings render with transparent backgrounds by default.
    Vision interprets transparent pixels as black, causing recognition to fail
    for black strokes (the entire image appears black to the recognizer).

    Solution: Composite the drawing onto a white background before recognition.

    In Swift/iOS:
        let renderer = UIGraphicsImageRenderer(size: drawing.bounds.size)
        let image = renderer.image { ctx in
            UIColor.white.setFill()
            ctx.fill(drawing.bounds)
            drawing.draw(in: drawing.bounds)
        }

    This ensures black strokes are visible against white, not black.
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
                "Vision framework not available. This code must run on macOS/iOS with PyObjC."
            )

        await asyncio.sleep(0)

        # Create request based on path
        if path == OCRPath.FAST:
            request = Vision.VNRecognizeTextRequest.alloc().init()
            request.recognitionLevel = Vision.VNRequestTextRecognitionLevelFast
        else:
            request = Vision.VNRecognizeTextRequest.alloc().init()
            request.recognitionLevel = Vision.VNRequestTextRecognitionLevelAccurate

        if self.use_language_correction and hasattr(request, "usesLanguageCorrection"):
            request.usesLanguageCorrection = True

        # In a real implementation: process image_data with VNImageRequestHandler

        # Simulate Vision processing result
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
            # Simulate bounding box (x, y, width, height)
            bbox = BoundingBox(
                x=VISION_DEFAULT_X_POSITION,
                y=VISION_DEFAULT_Y_POSITION + i * VISION_DEFAULT_LINE_HEIGHT,
                width=VISION_DEFAULT_LINE_WIDTH,
                height=VISION_DEFAULT_LINE_HEIGHT_BBOX,
                confidence=base_conf + random.uniform(
                    -VISION_CONFIDENCE_VARIANCE, VISION_CONFIDENCE_VARIANCE
                ),
            )
            line = LineResult(text=text, bounding_box=bbox, confidence=bbox.confidence)
            lines.append(line)

        return lines

    def correct_language(self, text: str) -> tuple[str, int]:
        """Apply language correction using Vision's built-in correction."""
        # In actual Vision, language correction is part of VNRecognizeTextRequest
        # Here we simulate by fixing common errors
        corrections = 0
        corrected = text

        # Example corrections
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

    def extract_structure(self, document: Document) -> StructuredDocument:
        """Extract paragraphs, tables, and entities from document."""
        # Basic structure extraction based on line grouping
        paragraphs = []
        tables = []
        entities = []

        # Group lines into paragraphs by vertical spacing (simple heuristic)
        lines = document.lines
        if not lines:
            return StructuredDocument(paragraphs, tables, entities)

        current_para_lines = [lines[0]]
        for i in range(1, len(lines)):
            prev_line = lines[i - 1]
            curr_line = lines[i]

            # If vertical gap is small, consider same paragraph
            gap = abs(
                curr_line.bounding_box.y
                - (prev_line.bounding_box.y + prev_line.bounding_box.height)
            )
            if gap < PARAGRAPH_VERTICAL_GAP_THRESHOLD:
                current_para_lines.append(curr_line)
            else:
                # Create paragraph
                para = self._create_paragraph(current_para_lines)
                paragraphs.append(para)
                current_para_lines = [curr_line]

        if current_para_lines:
            para = self._create_paragraph(current_para_lines)
            paragraphs.append(para)

        # Detect tables (simple heuristic: aligned columns)
        # This is a placeholder; real implementation would use column detection

        # Extract entities (emails, phones, URLs)
        for line in lines:
            line_entities = self._extract_entities_from_line(line)
            entities.extend(line_entities)

        return StructuredDocument(paragraphs, tables, entities)

    def _create_paragraph(self, lines: List[TextLine]) -> Paragraph:
        """Create a paragraph from a group of lines."""
        # Combined bounding box
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

        reading_order = 0  # placeholder; assign based on position

        return Paragraph(lines=lines, bounding_box=bbox, reading_order=reading_order)

    def _extract_entities_from_line(self, line: TextLine) -> List[Entity]:
        """Extract entities like email, phone, URL from a line."""
        import re

        entities = []
        text = line.text

        # Email regex
        email_pattern = r"[\w\.-]+@[\w\.-]+\.\w+"
        for match in re.finditer(email_pattern, text):
            start, end = match.span()
            entity_text = text[start:end]
            # Rough bbox estimation (simplified)
            bbox = BoundingBox(
                x=line.bounding_box.x + (start / len(text) * line.bounding_box.width),
                y=line.bounding_box.y,
                width=(end - start) / len(text) * line.bounding_box.width,
                height=line.bounding_box.height,
                confidence=line.confidence,
            )
            entity = Entity(
                entity_type=EntityType.EMAIL,
                value=entity_text,
                bounding_box=bbox,
                confidence=line.confidence,
            )
            entities.append(entity)

        # URL pattern
        url_pattern = r"https?://[^\s]+"
        for match in re.finditer(url_pattern, text):
            start, end = match.span()
            entity_text = text[start:end]
            bbox = BoundingBox(
                x=line.bounding_box.x + (start / len(text) * line.bounding_box.width),
                y=line.bounding_box.y,
                width=(end - start) / len(text) * line.bounding_box.width,
                height=line.bounding_box.height,
                confidence=line.confidence,
            )
            entity = Entity(
                entity_type=EntityType.URL,
                value=entity_text,
                bounding_box=bbox,
                confidence=line.confidence,
            )
            entities.append(entity)

        # Phone pattern (simple)
        phone_pattern = r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"
        for match in re.finditer(phone_pattern, text):
            start, end = match.span()
            entity_text = text[start:end]
            bbox = BoundingBox(
                x=line.bounding_box.x + (start / len(text) * line.bounding_box.width),
                y=line.bounding_box.y,
                width=(end - start) / len(text) * line.bounding_box.width,
                height=line.bounding_box.height,
                confidence=line.confidence,
            )
            entity = Entity(
                entity_type=EntityType.PHONE,
                value=entity_text,
                bounding_box=bbox,
                confidence=line.confidence,
            )
            entities.append(entity)

        return entities


# ===============================
# Custom Model Adapter (ANE-optimized)
# ===============================


class CustomModelOCRAdapter(OCREngine):
    """
    Adapter for custom OCR models optimized for Apple Neural Engine (ANE).
    Uses Core ML with conv layers and 1x1 convolutions instead of linear layers.
    """

    def __init__(self, model_path: str, use_ane: bool = True):
        super().__init__()
        self.model_path = model_path
        self.use_ane = use_ane
        self._model = None

        if os.path.exists(model_path):
            self._load_model()

    def _load_model(self) -> None:
        """Load Core ML model with ANE optimization if available."""
        try:
            import CoreML

            # Load model with compute units preference
            # MLModelConfiguration with computeUnits = .all (uses CPU, GPU, ANE)
            config = CoreML.MLModelConfiguration.alloc().init()
            if self.use_ane:
                config.computeUnits = CoreML.MLComputeUnitsAll  # .all includes ANE
            else:
                config.computeUnits = CoreML.MLComputeUnitsCPUOnly

            self._model = CoreML.MLModel.modelWithURL_configuration_(
                Path(self.model_path).absolute().as_uri(), config
            )
        except ImportError:
            # Fallback to mock
            self._model = None

    async def recognize(self, image_data: bytes, path: OCRPath) -> OCRResult:
        """Recognize text using custom model."""
        # In real implementation, would preprocess image, run model inference
        # using ANE-optimized layers

        await asyncio.sleep(0)

        if self._model is None:
            # Return mock results
            return self._mock_results()

        # Real inference would go here
        # Preprocess image to model input format
        # Call model.prediction...
        # Postprocess outputs (CTC decoding, bounding box refinement)

        return self._mock_results()

    def _mock_results(self) -> OCRResult:
        """Generate mock OCR results for demonstration."""
        lines = [
            LineResult(
                text="Custom model result",
                bounding_box=BoundingBox(
                    CUSTOM_MODEL_MOCK_X_POSITION,
                    CUSTOM_MODEL_MOCK_Y_POSITION_LINE1,
                    CUSTOM_MODEL_MOCK_LINE_WIDTH,
                    CUSTOM_MODEL_MOCK_LINE_HEIGHT,
                    CUSTOM_MODEL_MOCK_CONFIDENCE_HIGH,
                ),
                confidence=CUSTOM_MODEL_MOCK_CONFIDENCE_HIGH,
            ),
            LineResult(
                text="ANE-optimized architecture",
                bounding_box=BoundingBox(
                    CUSTOM_MODEL_MOCK_X_POSITION,
                    CUSTOM_MODEL_MOCK_Y_POSITION_LINE2,
                    CUSTOM_MODEL_MOCK_LINE2_WIDTH,
                    CUSTOM_MODEL_MOCK_LINE_HEIGHT,
                    CUSTOM_MODEL_MOCK_CONFIDENCE_MEDIUM,
                ),
                confidence=CUSTOM_MODEL_MOCK_CONFIDENCE_MEDIUM,
            ),
        ]
        return OCRResult(
            lines=lines,
            processing_time_ms=CUSTOM_MODEL_MOCK_PROCESSING_TIME_MS,
            average_confidence=CUSTOM_MODEL_MOCK_CONFIDENCE_AVG,
        )

    def correct_language(self, text: str) -> tuple[str, int]:
        """Apply language correction."""
        # Could integrate with a separate correction model or rules
        corrected = text.replace("0", "O").replace("1", "I")
        corrections = text.count("0") + text.count("1")
        return corrected, corrections

    def extract_structure(self, document: Document) -> StructuredDocument:
        """Extract structure using heuristics or separate model."""
        # For demo, reuse Vision logic
        vision_adapter = VisionOCRAdapter()
        return vision_adapter.extract_structure(document)


# ===============================
# File System Adapters
# ===============================


class LocalFileImageSource(ImageSource):
    """Adapter for reading images from local filesystem."""

    def __init__(self, base_path: str):
        super().__init__()
        self.base_path = Path(base_path)

    async def get_image(self, image_url: str) -> bytes:
        """
        Get image data from local file.
        image_url can be a relative path or absolute.
        """
        # Resolve path
        if image_url.startswith("file://"):
            image_url = image_url[7:]

        path = Path(image_url)
        if not path.is_absolute():
            path = self.base_path / path

        if not path.exists():
            raise FileNotFoundError(f"Image not found: {path}")

        # Read file asynchronously using to_thread
        return await asyncio.to_thread(path.read_bytes)

    async def exists(self, image_url: str) -> bool:
        """Check if image exists."""
        try:
            path = Path(image_url)
            if not path.is_absolute():
                path = self.base_path / path
            return path.exists()
        except Exception:
            return False


class InMemoryDocumentRepository(DocumentRepository):
    """In-memory repository for documents (for development/testing)."""

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


# ===============================
# HTTP Image Source Adapter
# ===============================


class HttpImageSource(ImageSource):
    """Adapter for fetching images via HTTP."""

    def __init__(self, timeout_seconds: float = HTTP_DEFAULT_TIMEOUT_SECONDS):
        super().__init__()
        self.timeout = timeout_seconds

    async def get_image(self, image_url: str) -> bytes:
        """Fetch image from HTTP URL."""
        import aiohttp

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        ) as session:
            async with session.get(image_url) as response:
                response.raise_for_status()
                return await response.read()

    async def exists(self, image_url: str) -> bool:
        """Check if URL exists (HEAD request)."""
        import aiohttp

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=HTTP_EXISTS_CHECK_TIMEOUT_SECONDS)
            ) as session:
                async with session.head(image_url) as response:
                    return response.status == 200
        except Exception:
            return False


# ===============================
# Configuration
# ===============================


class OCRConfig:
    """Configuration for OCR system."""

    def __init__(
        self,
        default_path: OCRPath = OCRPath.ACCURATE,
        use_language_correction: bool = True,
        temp_directory: str = "/tmp/ocr",
        max_image_size_mb: int = OCR_DEFAULT_MAX_IMAGE_SIZE_MB,
        enable_structured_extraction: bool = True,
    ):
        self.default_path = default_path
        self.use_language_correction = use_language_correction
        self.temp_directory = Path(temp_directory)
        self.max_image_size_mb = max_image_size_mb
        self.enable_structured_extraction = enable_structured_extraction

        # Ensure temp directory exists
        self.temp_directory.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_env(cls) -> OCRConfig:
        """Load configuration from environment variables."""
        import os

        path_str = os.getenv("OCR_DEFAULT_PATH", "accurate").lower()
        default_path = OCRPath.ACCURATE if path_str == "accurate" else OCRPath.FAST

        use_correction = os.getenv("OCR_USE_CORRECTION", "true").lower() == "true"

        temp_dir = os.getenv("OCR_TEMP_DIR", "/tmp/ocr")
        max_size = int(
            os.getenv("OCR_MAX_IMAGE_SIZE_MB", str(OCR_DEFAULT_MAX_IMAGE_SIZE_MB))
        )

        return cls(
            default_path=default_path,
            use_language_correction=use_correction,
            temp_directory=temp_dir,
            max_image_size_mb=max_size,
        )
