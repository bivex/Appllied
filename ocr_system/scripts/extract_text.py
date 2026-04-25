#!/usr/bin/env python3
"""
Extract text from images using Apple Vision framework.

This script uses VNRecognizeTextRequest to perform OCR on images.
Works on macOS/iOS with PyObjC bridge.

Usage:
    python extract_text.py image.png
    python extract_text.py image.png --accurate
    python extract_text.py image.png --languages en,fr,es
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from ocr_system.infrastructure.constants import (
    OCR_CONFIDENCE_FALLBACK,
    OCR_TOP_CANDIDATES_COUNT,
    OUTPUT_SEPARATOR_WIDTH,
)
from ocr_system.scripts.image_utils import fix_transparent_background

try:
    # Try to import Vision via PyObjC
    import Vision
    import CoreML
    import objc
    from Foundation import NSURL, NSData

    VISION_AVAILABLE = True
except ImportError:
    VISION_AVAILABLE = False
    print(
        "Warning: Vision framework not available. Install PyObjC: pip install pyobjc-framework-Vision pyobjc-framework-CoreML"
    )


def load_image_cgimage(image_path: Path) -> Optional[object]:
    """
    Load an image file and convert to CGImage.

    Uses Quartz/Core Graphics to decode the image.
    """
    try:
        from Quartz import (
            CGImageSourceCreateWithData,
            CGImageSourceCreateImageAtIndex,
        )
        from Foundation import NSData

        # Read file data
        data = NSData.dataWithContentsOfFile_(str(image_path))
        if data is None:
            print(f"Error: Could not read file {image_path}")
            return None

        # Create image source with options
        # kCGImageSourceShouldCache = True (default)
        options = None
        source = CGImageSourceCreateWithData(data, options)
        if source is None:
            print(f"Error: Could not create image source from {image_path}")
            return None

        # Get first image (index 0)
        # Options: None for default behavior
        cg_image = CGImageSourceCreateImageAtIndex(source, 0, None)
        if cg_image is None:
            print(f"Error: Could not decode image from {image_path}")
            return None

        return cg_image

    except ImportError as e:
        print(
            f"Error: Quartz framework not available ({e}). This script must run on macOS with PyObjC."
        )
        return None
    except Exception as e:
        print(f"Error loading image: {e}")
        return None


def _configure_vision_request(
    request,
    recognition_level: str,
    languages: Optional[List[str]],
    use_language_correction: bool,
    revision: Optional[int],
) -> None:
    """Configure a VNRecognizeTextRequest with recognition options."""
    # Set recognition level
    if recognition_level.lower() == "fast":
        request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelFast)
    else:
        request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)

    # Set languages
    if languages:
        request.setRecognitionLanguages_(languages)

    # Language correction
    if use_language_correction and hasattr(request, "usesLanguageCorrection"):
        request.setUsesLanguageCorrection_(use_language_correction)

    # Revision (for iOS 16+ handwriting improvements)
    if revision is not None and hasattr(request, "setRevision_"):
        request.setRevision_(revision)


def _collect_observations(observations) -> Tuple[List[str], float]:
    """Extract text and confidence from Vision observation results."""
    texts = []
    total_conf = 0.0
    count = 0

    for obs in observations:
        if hasattr(obs, "topCandidates_"):
            candidates = obs.topCandidates_(OCR_TOP_CANDIDATES_COUNT)
            if candidates and len(candidates) > 0:
                candidate = candidates[0]
                text = candidate.string()
                conf = candidate.confidence()
                texts.append(text)
                total_conf += conf
                count += 1
        else:
            # Fallback: try to get string directly
            if hasattr(obs, "string"):
                texts.append(obs.string())
                total_conf += OCR_CONFIDENCE_FALLBACK
                count += 1

    avg_conf = total_conf / count if count > 0 else 0.0
    return texts, avg_conf


def recognize_text(
    cg_image,
    recognition_level: str = "accurate",
    languages: List[str] = None,
    use_language_correction: bool = True,
    revision: Optional[int] = None,
) -> Tuple[List[str], float]:
    """
    Perform OCR on a CGImage using Vision.

    Args:
        cg_image: Core Graphics image (from CGImageSource)
        recognition_level: "fast" or "accurate"
        languages: List of BCP-47 language codes (e.g., ["en-US", "fr-FR"])
        use_language_correction: Enable spelling/grammar correction
        revision: Specific request revision (iOS 16+: 3 for handwriting)

    Returns:
        (list of recognized text strings, average confidence)
    """
    if not VISION_AVAILABLE:
        raise RuntimeError("Vision framework not available")

    # Create request
    request = Vision.VNRecognizeTextRequest.alloc().init()

    _configure_vision_request(
        request, recognition_level, languages, use_language_correction, revision
    )

    # Create handler
    handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(
        cg_image, None
    )

    # Perform request (synchronously)
    error = objc.NULL
    success = handler.performRequests_error_([request], error)
    # Handle the result properly
    if not success:
        # error is a pointer to NSError**
        if error[0] is not None:
            raise RuntimeError(
                f"Vision request failed: {error[0].localizedDescription()}"
            )
        else:
            raise RuntimeError("Vision request failed with unknown error")

    # Get results
    observations = request.results()
    if not observations:
        return [], 0.0

    return _collect_observations(observations)


def _validate_and_prepare(args) -> Tuple[Path, Optional[Path]]:
    """
    Validate arguments and prepare the image for OCR.

    Handles Vision availability check, image validation, transparent
    background fixing, and CGImage loading.

    Returns:
        Tuple of (image_path, temp_file_to_delete or None)
    """
    if not VISION_AVAILABLE:
        print("\nERROR: Vision framework is not available.")
        print("This script requires:")
        print("  1. macOS (or iOS with appropriate bridge)")
        print(
            "  2. PyObjC: pip install pyobjc-framework-Vision pyobjc-framework-CoreML"
        )
        print("\nAlternatively, use the OCRContainer from the Python implementation:")
        print("  from container import OCRContainer")
        print("  container = OCRContainer()")
        print("  result = await container.process_document(image_path)")
        sys.exit(1)

    # Validate image
    if not args.image.exists():
        print(f"Error: Image not found: {args.image}")
        sys.exit(1)

    # Handle transparent background (PKDrawing/PencilKit)
    to_delete = None
    image_path = args.image
    if not args.no_fix_bg:
        # Check if image has alpha channel
        try:
            from PIL import Image

            img = Image.open(image_path)
            if img.mode in ("RGBA", "LA", "P"):
                print(
                    "Detected transparent/masked image -- compositing onto white background..."
                )
                image_path = fix_transparent_background(image_path)
                to_delete = image_path  # cleanup later
        except ImportError:
            print(
                "Warning: Pillow not available -- skipping transparency check. Install: pip install Pillow"
            )

    return image_path, to_delete


def _format_output(texts: List[str], avg_conf: float, show_confidence: bool) -> str:
    """Format recognized text lines into the output string."""
    if show_confidence:
        return "\n".join(f"[{avg_conf:.2%}] {text}" for text in texts)
    return "\n".join(texts)


def _write_result(output: str, out_path, avg_conf: float, num_lines: int) -> None:
    """Write OCR result to file or console."""
    if out_path:
        out_path.write_text(output)
        print(f"Text saved to {out_path}")
    else:
        separator = "=" * OUTPUT_SEPARATOR_WIDTH
        print(f"\nRecognized Text:\n{separator}\n{output}\n{separator}")
        print(f"\nAverage confidence: {avg_conf:.2%}")
        print(f"Lines detected: {num_lines}")


def _build_parser() -> argparse.ArgumentParser:
    """Build argument parser for the OCR CLI."""
    parser = argparse.ArgumentParser(
        description="Extract text from images using Apple Vision OCR"
    )
    parser.add_argument("image", type=Path, help="Path to image file (PNG, JPG, etc.)")
    parser.add_argument("--level", "-l", choices=["fast", "accurate"], default="accurate",
                        help="Recognition level (default: accurate)")
    parser.add_argument("--languages", "-lang", type=str, default="en-US",
                        help="Comma-separated language codes (e.g. 'en-US,fr-FR')")
    parser.add_argument("--no-correction", action="store_true", help="Disable language correction")
    parser.add_argument("--handwriting", action="store_true",
                        help="Enable handwriting-optimized mode (iOS 16+ revision 3)")
    parser.add_argument("--no-fix-bg", action="store_true",
                        help="Don't auto-fix transparent backgrounds (PencilKit images)")
    parser.add_argument("--output", "-o", type=Path, default=None,
                        help="Save extracted text to file instead of stdout")
    parser.add_argument("--confidence", action="store_true", help="Show confidence scores")
    return parser


def main():
    args = _build_parser().parse_args()

    # Validate and prepare image
    image_path, to_delete = _validate_and_prepare(args)

    # Load image as CGImage
    cg_image = load_image_cgimage(image_path)
    if cg_image is None:
        sys.exit(1)

    # Parse languages
    langs = [lang.strip() for lang in args.languages.split(",")]

    # Set revision for handwriting
    revision = None
    if args.handwriting:
        try:
            revision = Vision.VNRecognizeTextRequestRevision3
        except AttributeError:
            print("Warning: VNRecognizeTextRequestRevision3 not available (requires iOS 16+/macOS 13+)")

    # Recognize
    try:
        texts, avg_conf = recognize_text(
            cg_image=cg_image,
            recognition_level=args.level,
            languages=langs,
            use_language_correction=not args.no_correction,
            revision=revision,
        )
    except Exception as e:
        print(f"Recognition failed: {e}")
        sys.exit(1)

    # Format and write output
    output = _format_output(texts, avg_conf, args.confidence)
    _write_result(output, args.output, avg_conf, len(texts))

    # Cleanup temp file
    if to_delete and to_delete != args.image:
        to_delete.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
