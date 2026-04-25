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
            kCGImageTypeIdentifierPNG,
        )
        from Foundation import NSData, NSURL

        # Read file data
        data = NSData.dataWithContentsOfFile_(str(image_path))

        # Create image source
        source = CGImageSourceCreateWithData(data, None)
        if source is None:
            print(f"Error: Could not create image source from {image_path}")
            return None

        # Get first image
        cg_image = CGImageSourceCreateImageAtIndex(source, 0, None)
        if cg_image is None:
            print(f"Error: Could not decode image from {image_path}")
            return None

        return cg_image

    except ImportError:
        print(
            "Error: Quartz framework not available. This script must run on macOS with PyObjC."
        )
        return None
    except Exception as e:
        print(f"Error loading image: {e}")
        return None


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

    # Create handler
    handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(
        cg_image, None
    )

    # Perform request (synchronously)
    import objc

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

    texts = []
    total_conf = 0.0
    count = 0

    for obs in observations:
        if hasattr(obs, "topCandidates_"):
            candidates = obs.topCandidates_(1)
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
                total_conf += 0.5  # unknown confidence
                count += 1

    avg_conf = total_conf / count if count > 0 else 0.0
    return texts, avg_conf


def fix_transparent_background(
    image_path: Path, output_path: Optional[Path] = None
) -> Path:
    """
    Composite an RGBA image onto a white background to avoid Vision's
    transparent→black interpretation issue.

    Args:
        image_path: Path to input image (may have alpha)
        output_path: Where to save composited image (if None, temp file)

    Returns:
        Path to composited image
    """
    try:
        from PIL import Image
    except ImportError:
        print("Error: Pillow required for background compositing. pip install Pillow")
        exit(1)

    img = Image.open(image_path)

    if img.mode in ("RGBA", "LA"):
        # Create white background
        background = Image.new("RGB", img.size, (255, 255, 255))
        # Composite using alpha as mask
        background.paste(
            img, mask=img.split()[-1] if img.mode == "RGBA" else img.split()[-1]
        )
        result = background
    else:
        result = img.convert("RGB")

    if output_path is None:
        output_path = image_path.parent / f"composited_{image_path.name}"

    result.save(output_path)
    print(f"Composited image saved: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Extract text from images using Apple Vision OCR"
    )
    parser.add_argument("image", type=Path, help="Path to image file (PNG, JPG, etc.)")
    parser.add_argument(
        "--level",
        "-l",
        choices=["fast", "accurate"],
        default="accurate",
        help="Recognition level (default: accurate)",
    )
    parser.add_argument(
        "--languages",
        "-lang",
        type=str,
        default="en-US",
        help="Comma-separated language codes (e.g. 'en-US,fr-FR')",
    )
    parser.add_argument(
        "--no-correction", action="store_true", help="Disable language correction"
    )
    parser.add_argument(
        "--handwriting",
        action="store_true",
        help="Enable handwriting-optimized mode (iOS 16+ revision 3)",
    )
    parser.add_argument(
        "--no-fix-bg",
        action="store_true",
        help="Don't auto-fix transparent backgrounds (PencilKit images)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Save extracted text to file instead of stdout",
    )
    parser.add_argument(
        "--confidence", action="store_true", help="Show confidence scores"
    )

    args = parser.parse_args()

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
        exit(1)

    # Validate image
    if not args.image.exists():
        print(f"Error: Image not found: {args.image}")
        exit(1)

    # Parse languages
    langs = [lang.strip() for lang in args.languages.split(",")]

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
                    "Detected transparent/masked image — compositing onto white background..."
                )
                image_path = fix_transparent_background(image_path)
                to_delete = image_path  # cleanup later
        except ImportError:
            print(
                "Warning: Pillow not available — skipping transparency check. Install: pip install Pillow"
            )

    # Load image as CGImage
    cg_image = load_image_cgimage(image_path)
    if cg_image is None:
        exit(1)

    # Set revision for handwriting
    revision = None
    if args.handwriting:
        try:
            revision = Vision.VNRecognizeTextRequestRevision3
        except AttributeError:
            print(
                "Warning: VNRecognizeTextRequestRevision3 not available (requires iOS 16+/macOS 13+)"
            )

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
        exit(1)

    # Format output
    if args.confidence:
        output_lines = []
        for text in texts:
            output_lines.append(f"[{avg_conf:.2%}] {text}")
        output = "\n".join(output_lines)
    else:
        output = "\n".join(texts)

    # Write output
    if args.output:
        args.output.write_text(output)
        print(f"Text saved to {args.output}")
    else:
        print("\nRecognized Text:")
        print("=" * 60)
        print(output)
        print("=" * 60)
        print(f"\nAverage confidence: {avg_conf:.2%}")
        print(f"Lines detected: {len(texts)}")

    # Cleanup temp file
    if to_delete and to_delete != args.image:
        to_delete.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
