"""Domain services for application layer."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from domain import Language, OCRPath

# Constants for path selection strategy
MEGAPIXELS_THRESHOLD = 2.0
TEXT_DENSITY_THRESHOLD = 0.3
PROCESSING_TIME_PER_MEGAPIXEL_FAST = 10  # ms
PROCESSING_TIME_PER_MEGAPIXEL_ACCURATE = 100  # ms


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
    ) -> OCRPath:
        ...

    def estimate_processing_time(
        self, path: OCRPath, image_size: tuple[int, int]
    ) -> float:
        """Estimate processing time in milliseconds."""
        width, height = image_size
        pixels = width * height

        if path == OCRPath.FAST:
            return pixels / 1_000_000 * PROCESSING_TIME_PER_MEGAPIXEL_FAST
        else:
            return pixels / 1_000_000 * PROCESSING_TIME_PER_MEGAPIXEL_ACCURATE


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
        megapixels = (width * height) / 1_000_000

        # Use fast path for small images or high text density
        if megapixels < MEGAPIXELS_THRESHOLD or estimated_text_density > TEXT_DENSITY_THRESHOLD:
            return OCRPath.FAST

        # Use accurate path for larger images with sparse text
        return OCRPath.ACCURATE
