#!/usr/bin/env python3
"""
Extract text from PDF files using Apple Vision framework.

Uses Vision's document analysis capabilities to perform OCR on PDF pages.
Works on macOS with PyObjC bridge.

Usage:
    python extract_text_from_pdf.py document.pdf
    python extract_text_from_pdf.py document.pdf --pages 1-3,5
    python extract_text_from_pdf.py document.pdf --output text.txt
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Tuple

try:
    import Vision
    import CoreML
    from Quartz import (
        CGImageSourceCreateWithURL,
        CGImageSourceCreateImageAtIndex,
        kCGImageSourceShouldCache,
    )
    from Foundation import NSURL, NSDictionary

    VISION_AVAILABLE = True
except ImportError:
    VISION_AVAILABLE = False


def load_pdf_pages(
    pdf_path: Path, page_range: Optional[List[int]] = None
) -> List[object]:
    """
    Load PDF pages as CGImage objects.

    Args:
        pdf_path: Path to PDF file
        page_range: Optional list of page numbers (1-based) to process.
                   If None, all pages are processed.

    Returns:
        List of CGImage objects, one per page
    """
    try:
        from Quartz import (
            CGPDFDocumentCreateWithURL,
            CGPDFDocumentGetNumberOfPages,
            CGPDFDocumentGetPage,
            CGPDFPageGetBoxRect,
            kCGPDFMediaBox,
        )
    except ImportError:
        print("Error: Quartz framework not available. Install PyObjC.")
        return []

    # Create URL
    url = NSURL.fileURLWithPath_(str(pdf_path.absolute()))

    # Create PDF document
    pdf = CGPDFDocumentCreateWithURL(url)
    if pdf is None:
        print(f"Error: Could not open PDF: {pdf_path}")
        return []

    # Get page count
    num_pages = CGPDFDocumentGetNumberOfPages(pdf)
    print(f"PDF has {num_pages} pages")

    # Determine which pages to process
    if page_range is None:
        pages_to_process = list(range(1, num_pages + 1))
    else:
        pages_to_process = [p for p in page_range if 1 <= p <= num_pages]

    print(f"Processing pages: {pages_to_process}")

    cg_images = []
    for page_num in pages_to_process:
        # Get page
        page = CGPDFDocumentGetPage(pdf, page_num)
        if page is None:
            print(f"Warning: Could not load page {page_num}")
            continue

        # Get page rect
        rect = CGPDFPageGetBoxRect(page, kCGPDFMediaBox)

        # Render page to CGImage
        # Use a bitmap context to rasterize the PDF page
        from Quartz import (
            CGBitmapContextCreate,
            CGColorSpaceCreateDeviceRGB,
            CGImageDestinationCreateWithURL,
            CGImageDestinationAddImage,
            CGImageDestinationFinalize,
        )
        import math

        width = int(rect.size.width)
        height = int(rect.size.height)

        # Create bitmap context
        color_space = CGColorSpaceCreateDeviceRGB()
        context = CGBitmapContextCreate(
            None,  # let Quartz allocate
            width,
            height,
            8,  # bits per component
            0,  # bytes per row (0 = auto)
            color_space,
            0x1F00,  # kCGImageAlphaPremultipliedFirst | kCGBitmapByteOrder32Little (RGBA)
        )

        if context is None:
            print(f"Warning: Could not create context for page {page_num}")
            continue

        # Draw PDF page into context (white background)
        from Quartz import (
            CGContextSetFillColorSpace,
            CGContextSetFillColor,
            CGContextFillRect,
            CGContextDrawPDFPage,
        )

        white = [1.0, 1.0, 1.0, 1.0]
        CGContextSetFillColor(context, white)
        CGContextFillRect(context, rect)
        CGContextDrawPDFPage(context, page)

        # Extract CGImage from context
        from Quartz import CGBitmapContextCreateImage

        cg_image = CGBitmapContextCreateImage(context)

        if cg_image:
            cg_images.append(cg_image)
        else:
            print(f"Warning: Could not create image for page {page_num}")

    return cg_images


def recognize_text_from_cgimage(
    cg_image,
    recognition_level: str = "accurate",
    languages: List[str] = None,
    use_language_correction: bool = True,
    revision: Optional[int] = None,
) -> Tuple[List[str], float]:
    """
    Perform OCR on a CGImage using Vision.

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

    # Revision for handwriting (iOS 16+)
    if revision is not None and hasattr(request, "setRevision_"):
        request.setRevision_(revision)

    # Create handler
    handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(
        cg_image, None
    )

    # Perform
    import objc

    error = objc.NULL
    success = handler.performRequests_error_([request], error)
    if not success:
        if error[0] is not None:
            raise RuntimeError(
                f"Vision request failed: {error[0].localizedDescription()}"
            )
        else:
            raise RuntimeError("Vision request failed")

    # Extract results
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
        elif hasattr(obs, "string"):
            texts.append(obs.string())
            total_conf += 0.5
            count += 1

    avg_conf = total_conf / count if count > 0 else 0.0
    return texts, avg_conf


def parse_page_range(page_range_str: str) -> List[int]:
    """
    Parse page range string like "1-3,5,7-9" into list of 1-based page numbers.

    Examples:
        "1-5" -> [1, 2, 3, 4, 5]
        "1,3,5" -> [1, 3, 5]
        "1-3,5,7-9" -> [1, 2, 3, 5, 7, 8, 9]
    """
    pages = set()
    for part in page_range_str.split(","):
        part = part.strip()
        if "-" in part:
            try:
                start, end = map(int, part.split("-"))
                if start > end:
                    start, end = end, start
                pages.update(range(start, end + 1))
            except ValueError:
                raise ValueError(f"Invalid page range: {part}")
        else:
            try:
                pages.add(int(part))
            except ValueError:
                raise ValueError(f"Invalid page number: {part}")
    return sorted(pages)


def main():
    parser = argparse.ArgumentParser(
        description="Extract text from PDF files using Apple Vision OCR"
    )
    parser.add_argument("pdf", type=Path, help="Path to PDF file")
    parser.add_argument(
        "--pages",
        "-p",
        type=str,
        default=None,
        help="Page range (e.g., '1-3,5,7-9' or 'all' for all pages)",
    )
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
        help="Comma-separated language codes (default: en-US)",
    )
    parser.add_argument(
        "--no-correction", action="store_true", help="Disable language correction"
    )
    parser.add_argument(
        "--handwriting",
        action="store_true",
        help="Enable handwriting-optimized mode (iOS 16+/macOS 13+)",
    )
    parser.add_argument(
        "--output", "-o", type=Path, default=None, help="Save extracted text to file"
    )
    parser.add_argument(
        "--separator",
        type=str,
        default="\n\n",
        help="Separator between pages (default: double newline)",
    )
    parser.add_argument(
        "--confidence", action="store_true", help="Show confidence scores per page"
    )

    args = parser.parse_args()

    if not VISION_AVAILABLE:
        print("\nERROR: Vision framework not available.")
        print(
            "Install PyObjC: pip install pyobjc-framework-Vision pyobjc-framework-CoreML"
        )
        print("This script requires macOS.")
        sys.exit(1)

    # Validate PDF
    if not args.pdf.exists():
        print(f"Error: PDF not found: {args.pdf}")
        sys.exit(1)

    # Parse page range
    page_range = None
    if args.pages:
        if args.pages.lower() == "all":
            page_range = None
        else:
            try:
                page_range = parse_page_range(args.pages)
            except ValueError as e:
                print(f"Error: {e}")
                sys.exit(1)

    # Parse languages
    langs = [lang.strip() for lang in args.languages.split(",")]

    # Set revision for handwriting
    revision = None
    if args.handwriting:
        try:
            revision = Vision.VNRecognizeTextRequestRevision3
        except AttributeError:
            print("Warning: Revision 3 not available (requires iOS 16+/macOS 13+)")

    # Load PDF pages
    print(f"Loading PDF: {args.pdf}")
    cg_images = load_pdf_pages(args.pdf, page_range)

    if not cg_images:
        print("Error: No pages could be loaded from PDF")
        sys.exit(1)

    print(f"Successfully loaded {len(cg_images)} page(s)")

    # Process each page
    all_texts = []
    all_confidences = []

    for i, cg_image in enumerate(cg_images, 1):
        print(f"Processing page {i}/{len(cg_images)}...", end=" ", flush=True)
        try:
            texts, avg_conf = recognize_text_from_cgimage(
                cg_image=cg_image,
                recognition_level=args.level,
                languages=langs,
                use_language_correction=not args.no_correction,
                revision=revision,
            )
            page_text = "\n".join(texts)
            all_texts.append(page_text)
            all_confidences.append(avg_conf)
            print(f"done (conf: {avg_conf:.2%}, {len(texts)} lines)")
        except Exception as e:
            print(f"ERROR: {e}")
            all_texts.append(f"[ERROR processing page {i}]")
            all_confidences.append(0.0)

    # Combine pages
    separator = args.separator
    full_text = separator.join(all_texts)

    # Calculate overall confidence
    overall_conf = (
        sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
    )

    # Output
    if args.output:
        args.output.write_text(full_text)
        print(f"\nText saved to: {args.output}")
    else:
        print("\n" + "=" * 60)
        print("EXTRACTED TEXT")
        print("=" * 60)
        if args.confidence:
            for i, (text, conf) in enumerate(zip(all_texts, all_confidences), 1):
                print(f"\n--- Page {i} [{conf:.2%}] ---")
                print(text)
        else:
            print(full_text)
        print("=" * 60)
        print(f"\nPages processed: {len(all_texts)}")
        print(f"Overall confidence: {overall_conf:.2%}")
        print(f"Total characters: {len(full_text)}")

    # Summary
    if all_confidences:
        min_conf = min(all_confidences)
        max_conf = max(all_confidences)
        print(f"\nConfidence range: {min_conf:.2%} - {max_conf:.2%}")


if __name__ == "__main__":
    main()
