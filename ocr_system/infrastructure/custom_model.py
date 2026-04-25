"""
Custom Model Adapter optimized for Apple Neural Engine (ANE).

Uses Core ML with conv layers and 1x1 convolutions instead of linear layers
for better ANE efficiency.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import List

from ..application import OCREngine, OCRResult, LineResult
from ..domain import BoundingBox, OCRPath, Document
from .constants import (
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
)
from .vision import VisionOCRAdapter  # reuse for structure extraction
from ..application import StructuredDocument


class CustomModelOCRAdapter(OCREngine):
    """Adapter for custom OCR models optimized for ANE."""

    def __init__(self, model_path: str, use_ane: bool = True):
        super().__init__()
        self.model_path = model_path
        self.use_ane = use_ane
        self._model = None

        if os.path.exists(model_path):
            self._load_model()

    def _load_model(self) -> None:
        """Load Core ML model with ANE optimization."""
        try:
            import CoreML

            config = CoreML.MLModelConfiguration.alloc().init()
            if self.use_ane:
                config.computeUnits = CoreML.MLComputeUnitsAll
            else:
                config.computeUnits = CoreML.MLComputeUnitsCPUOnly

            self._model = CoreML.MLModel.modelWithURL_configuration_(
                Path(self.model_path).absolute().as_uri(), config
            )
        except ImportError:
            self._model = None

    async def recognize(self, image_data: bytes, path: OCRPath) -> OCRResult:
        """Recognize text using custom model."""
        await asyncio.sleep(0)

        if self._model is None:
            return self._mock_results()

        # Real inference would go here
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
        corrected = text.replace("0", "O").replace("1", "I")
        corrections = text.count("0") + text.count("1")
        return corrected, corrections

    def extract_structure(self, document: Document) -> StructuredDocument:
        """Extract structure using heuristics."""
        vision_adapter = VisionOCRAdapter()
        return vision_adapter.extract_structure(document)
