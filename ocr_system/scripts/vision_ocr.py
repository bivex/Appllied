#!/usr/bin/env python3
"""
Vision OCR utilities using Apple Vision framework.

Performs text recognition on CGImage objects.
"""

from __future__ import annotations

from typing import List, Tuple

from ocr_system.infrastructure.constants import (
    OCR_CONFIDENCE_FALLBACK,
    OCR_TOP_CANDIDATES_COUNT,
)

# Check Vision availability
try:
    import Vision
    import CoreML
    import objc
    VISION_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import required frameworks: {e}")
    VISION_AVAILABLE = False


def _configure_request(request, recognition_level: str, languages, use_language_correction: bool, revision):
    """Apply recognition settings to a VNRecognizeTextRequest."""
    if recognition_level.lower() == "fast":
        request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelFast)
    else:
        request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)

    if languages:
        request.setRecognitionLanguages_(languages)

    if use_language_correction and hasattr(request, "usesLanguageCorrection"):
        request.setUsesLanguageCorrection_(use_language_correction)

    if revision is not None and hasattr(request, "setRevision_"):
        request.setRevision_(revision)


def _perform_vision_request(handler, request) -> List:
    """Execute a Vision request and return observations, raising on failure."""
    error = objc.NULL
    success = handler.performRequests_error_([request], error)
    if not success:
        if error[0] is not None:
            raise RuntimeError(f"Vision error: {error[0].localizedDescription()}")
        else:
            raise RuntimeError("Vision request failed")

    observations = request.results()
    return observations if observations else []


def _extract_text_from_observations(observations) -> Tuple[List[str], float]:
    """Collect recognized text and compute average confidence."""
    texts = []
    total_conf = 0.0
    count = 0

    for obs in observations:
        if hasattr(obs, "topCandidates_"):
            candidates = obs.topCandidates_(OCR_TOP_CANDIDATES_COUNT)
            if candidates and len(candidates) > 0:
                texts.append(candidates[0].string())
                total_conf += candidates[0].confidence()
                count += 1
        elif hasattr(obs, "string"):
            texts.append(obs.string())
            total_conf += OCR_CONFIDENCE_FALLBACK
            count += 1

    avg_conf = total_conf / count if count > 0 else 0.0
    return texts, avg_conf


def recognize_text_from_cgimage(
    cg_image,
    recognition_level: str = "accurate",
    languages: List[str] = None,
    use_language_correction: bool = True,
    revision=None,
) -> Tuple[List[str], float]:
    """Perform OCR on CGImage using Vision."""
    request = Vision.VNRecognizeTextRequest.alloc().init()
    _configure_request(request, recognition_level, languages, use_language_correction, revision)

    handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(
        cg_image, None
    )

    observations = _perform_vision_request(handler, request)
    if not observations:
        return [], 0.0

    return _extract_text_from_observations(observations)
