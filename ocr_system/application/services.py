"""Domain services for application layer."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from ..domain import Language, OCRPath

from ocr_system.infrastructure.constants import (
    PATH_SELECTION_MEGAPIXEL_THRESHOLD,
    PATH_SELECTION_TEXT_DENSITY_THRESHOLD,
    PIXELS_PER_MEGAPIXEL,
)

# Processing time estimation constants
PROCESSING_TIME_PER_MEGAPIXEL_FAST = 10
PROCESSING_TIME_PER_MEGAPIXEL_ACCURATE = 100


class LanguageCorrectionService:
    """Domain service for correcting OCR text based on language rules."""

    def __init__(self, language: Language):
        self.language = language

    def correct(self, text: str) -> tuple[str, int]:
        """
        Apply language-specific corrections.
        Returns corrected text and number of corrections made.
        """
        corrections = 0
        corrected = text

        # Common OCR errors and their corrections based on language
        # This is a simplified example - real implementation would use dictionaries
        common_errors = {
            "0": "O",  # zero -> capital O
            "1": "I",  # one -> capital I
            "5": "S",  # five -> capital S
            "8": "B",  # eight -> capital B
        }

        for error, correction in common_errors.items():
            if error in corrected:
                corrected = corrected.replace(error, correction)
                corrections += corrected.count(error)

        return corrected, corrections


class PathSelectionStrategy(ABC):
    """Strategy for selecting OCR processing path."""

    @abstractmethod
    def select_path(
        self,
        image_size: tuple[int, int],
        estimated_text_density: float,
        language_hint: Optional[Language],
    ) -> OCRPath: ...

    def estimate_processing_time(
        self, path: OCRPath, image_size: tuple[int, int]
    ) -> float:
        """Estimate processing time in milliseconds."""
        width, height = image_size
        pixels = width * height

        if path == OCRPath.FAST:
            return pixels / PIXELS_PER_MEGAPIXEL * PROCESSING_TIME_PER_MEGAPIXEL_FAST
        else:
            return (
                pixels / PIXELS_PER_MEGAPIXEL * PROCESSING_TIME_PER_MEGAPIXEL_ACCURATE
            )


class SimplePathSelectionStrategy(PathSelectionStrategy):
    """Simple heuristic-based path selection."""

    def select_path(
        self,
        image_size: tuple[int, int],
        estimated_text_density: float,
        language_hint: Optional[Language],
    ) -> OCRPath:
        """Select FAST or ACCURATE based on image characteristics."""
        width, height = image_size
        megapixels = (width * height) / PIXELS_PER_MEGAPIXEL

        if (
            megapixels < PATH_SELECTION_MEGAPIXEL_THRESHOLD
            or estimated_text_density > PATH_SELECTION_TEXT_DENSITY_THRESHOLD
        ):
            return OCRPath.FAST

        # Use accurate path for larger images with sparse text
        return OCRPath.ACCURATE
