"""
OCR System - Infrastructure Layer.

Adapters for external services: Vision framework, file system, databases.
Implements ports defined in application layer.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Dict, List, Optional
from uuid import UUID

from ..application import (
    OCREngine,
    OCRResult,
    LineResult,
    StructuredDocument,
    DocumentRepository,
    ImageSource,
)
from ..domain import (
    Document,
    DocumentType,
    TextLine,
    BoundingBox,
    OCRPath,
    Paragraph,
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
    PATH_SELECTION_MEGAPIXEL_THRESHOLD,
    PATH_SELECTION_TEXT_DENSITY_THRESHOLD,
    PIXELS_PER_MEGAPIXEL,
)
from .entity_extraction import EntityExtractor

# Re-export adapters from submodules for backward compatibility
from .vision import VisionOCRAdapter
from .custom_model import CustomModelOCRAdapter
from .repositories import InMemoryDocumentRepository
from .sources import LocalFileImageSource, HttpImageSource

__all__ = [
    # Adapters
    "VisionOCRAdapter",
    "CustomModelOCRAdapter",
    "InMemoryDocumentRepository",
    "LocalFileImageSource",
    "HttpImageSource",
    # Config
    "OCRConfig",
    # Constants (commonly used)
    "VISION_FAST_PROCESSING_TIME_MS",
    "VISION_ACCURATE_PROCESSING_TIME_MS",
    "OCR_DEFAULT_MAX_IMAGE_SIZE_MB",
]


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
