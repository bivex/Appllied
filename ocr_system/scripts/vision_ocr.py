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
    VISION_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import required frameworks: {e}")
    VISION_AVAILABLE = False


def recognize_text_from_cgimage(
    cg_image,
    recognition_level: str = "accurate",
    languages: List[str] = None,
    use_language_correction: bool = True,
    revision=None,
) -> Tuple[List[str], float]:
    """Perform OCR on CGImage using Vision."""
    request = Vision.VNRecognizeTextRequest.alloc().init()

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

    handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(
        cg_image, None
    )

    import objc
    error = objc.NULL
    success = handler.performRequests_error_([request], error)
    if not success:
        if error[0] is not None:
            raise RuntimeError(f"Vision error: {error[0].localizedDescription()}")
        else:
            raise RuntimeError("Vision request failed")

    observations = request.results()
    if not observations:
        return [], 0.0

    texts = []
    total_conf = 0.0
    count = 0

    for obs in observations:
        if hasattr(obs, "topCandidates_"):
            candidates = obs.topCandidates_(OCR_TOP_CANDIDATES_COUNT)
            if candidates and len(candidates) > 0:
                candidate = candidates[0]
                texts.append(candidate.string())
                total_conf += candidate.confidence()
                count += 1
        elif hasattr(obs, "string"):
            texts.append(obs.string())
            total_conf += OCR_CONFIDENCE_FALLBACK
            count += 1

    avg_conf = total_conf / count if count > 0 else 0.0
    return texts, avg_conf
