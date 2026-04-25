#!/usr/bin/env python3
"""
Extract text from PDF files using Apple Vision framework (simplified version).

Renders PDF pages to images using Quartz and runs Vision OCR.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Tuple

# Check Vision availability
try:
    import Vision
    import CoreML
    from Quartz import (
        CGPDFDocumentCreateWithURL,
        CGPDFDocumentGetNumberOfPages,
        CGPDFDocumentGetPage,
        CGPDFPageGetBoxRect,
        kCGPDFMediaBox,
        CGBitmapContextCreate,
        CGColorSpaceCreateDeviceRGB,
        CGBitmapContextCreateImage,
        CGContextSetRGBFillColor,
        CGContextFillRect,
        CGContextDrawPDFPage,
        CGImageAlphaInfo,
    )
    from Foundation import NSURL
    VISION_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import required frameworks: {e}")
    VISION_AVAILABLE = False


def render_pdf_page_to_cgimage(pdf_url, page_num: int, scale: float = 2.0):
    """
    Render a single PDF page to CGImage.

    Args:
        pdf_url: NSURL to PDF file
        page_num: 1-based page number
        scale: Scale factor for rendering (2.0 = 2x resolution)

    Returns:
        CGImage object or None
    """
    # Create PDF document
    pdf = CGPDFDocumentCreateWithURL(pdf_url)
    if pdf is None:
        print(f"  Error: Could not open PDF")
        return None

    # Get page
    page = CGPDFDocumentGetPage(pdf, page_num)
    if page is None:
        print(f"  Error: Could not get page {page_num}")
        return None

    # Get page rect
    rect = CGPDFPageGetBoxRect(page, kCGPDFMediaBox)
    width = int(rect.size.width * scale)
    height = int(rect.size.height * scale)

    if width <= 0 or height <= 0:
        print(f"  Error: Invalid dimensions {width}x{height}")
        return None

    print(f"  Rendering at {width}x{height} (scale {scale}x)")

    # Create bitmap context
    color_space = CGColorSpaceCreateDeviceRGB()

    # Bitmap info: RGBA, premultiplied alpha, little-endian
    # CGImageAlphaPremultipliedFirst | kCGBitmapByteOrder32Little
    bitmap_info = 1 | 0x2000  # kCGImageAlphaPremultipliedFirst | kCGBitmapByteOrder32Little

    context = CGBitmapContextCreate(
        None,      # data (NULL = let Quartz allocate)
        width,
        height,
        8,         # bits per component
        0,         # bytes per row (0 = auto)
        color_space,
        bitmap_info
    )

    if context is None:
        print(f"  Error: Could not create bitmap context")
        return None

    # Fill white background (important for Vision)
    CGContextSetRGBFillColor(context, 1.0, 1.0, 1.0, 1.0)
    CGContextFillRect(context, rect)

    # Draw PDF page (apply scale transform)
    from Quartz import CGContextScaleCTM, CGContextConcatCTM, CGAffineTransformMakeScale
    transform = CGAffineTransformMakeScale(scale, scale)
    CGContextConcatCTM(context, transform)

    CGContextDrawPDFPage(context, page)

    # Extract CGImage
    cg_image = CGBitmapContextCreateImage(context)
    return cg_image


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


def parse_page_range(s: str) -> List[int]:
    """Parse '1-3,5,7-9' into [1,2,3,5,7,8,9]."""
    pages = set()
    for part in s.split(","):
        part = part.strip()
        if "-" in part:
            start, end = map(int, part.split("-"))
            pages.update(range(min(start, end), max(start, end) + 1))
        else:
            pages.add(int(part))
    return sorted(pages)


def main():
    parser = argparse.ArgumentParser(
        description="Extract text from PDF using Apple Vision OCR"
    )
    parser.add_argument("pdf", type=Path, help="PDF file path")
    parser.add_argument("--pages", "-p", type=str, default=None,
                        help="Page range (e.g., '1-3,5' or 'all')")
    parser.add_argument("--level", "-l", choices=["fast", "accurate"], default="accurate",
                        help="Recognition level")
    parser.add_argument("--languages", "-lang", type=str, default="en-US",
                        help="Comma-separated BCP-47 codes")
    parser.add_argument("--no-correction", action="store_true",
                        help="Disable language correction")
    parser.add_argument("--handwriting", action="store_true",
                        help="Use handwriting-optimized mode (iOS 16+)")
    parser.add_argument("--output", "-o", type=Path, default=None,
                        help="Save to file")
    parser.add_argument("--separator", type=str, default="\n\n",
                        help="Page separator")
    parser.add_argument("--confidence", action="store_true",
                        help="Show confidence per page")
    parser.add_argument("--scale", type=float, default=2.0,
                        help="Render scale factor (default: 2.0)")

    args = parser.parse_args()

    if not VISION_AVAILABLE:
        print("\nERROR: Vision/Quartz not available.")
        print("Install: pip install pyobjc-framework-Vision pyobjc-framework-CoreML")
        print("Requires macOS.")
        sys.exit(1)

    if not args.pdf.exists():
        print(f"Error: PDF not found: {args.pdf}")
        sys.exit(1)

    # Parse pages
    if args.pages:
        if args.pages.lower() == "all":
            page_range = None
        else:
            try:
                page_range = parse_page_range(args.pages)
            except ValueError as e:
                print(f"Error: {e}")
                sys.exit(1)
    else:
        page_range = None

    # Languages
    langs = [l.strip() for l in args.languages.split(",")]

    # Revision for handwriting
    revision = None
    if args.handwriting:
        try:
            revision = Vision.VNRecognizeTextRequestRevision3
        except AttributeError:
            print("Warning: Revision 3 not available (requires macOS 13+)")

    # Create URL
    pdf_url = NSURL.fileURLWithPath_(str(args.pdf.absolute()))

    # Get page count (for info)
    from Quartz import CGImageSourceCreateWithURL, CGImageSourceGetCount
    source = CGImageSourceCreateWithURL(pdf_url, None)
    if source:
        total_pages = CGImageSourceGetCount(source)
        print(f"PDF: {total_pages} page(s)")
    else:
        print("Warning: Could not get page count via CGImageSource")
        total_pages = 1  # fallback

    # Determine which pages to process
    if page_range is None:
        pages = list(range(1, total_pages + 1))
    else:
        pages = [p for p in page_range if 1 <= p <= total_pages]

    print(f"Will process pages: {pages}")
    print(f"Render scale: {args.scale}x")

    # Process pages
    all_texts = []
    all_confs = []

    for p in pages:
        print(f"\nPage {p}/{len(pages)}...", flush=True)
        cg_img = render_pdf_page_to_cgimage(pdf_url, p, scale=args.scale)
        if cg_img is None:
            print(f"  Failed to render page {p}")
            all_texts.append(f"[Error: page {p} could not be rendered]")
            all_confs.append(0.0)
            continue

        print(f"  Running Vision OCR...", flush=True)
        try:
            texts, conf = recognize_text_from_cgimage(
                cg_img,
                recognition_level=args.level,
                languages=langs,
                use_language_correction=not args.no_correction,
                revision=revision,
            )
            page_text = "\n".join(texts)
            all_texts.append(page_text)
            all_confs.append(conf)
            print(f"  ✓ {len(texts)} lines, avg conf: {conf:.2%}")
        except Exception as e:
            print(f"  ✗ OCR failed: {e}")
            all_texts.append(f"[Error: OCR failed on page {p}]")
            all_confs.append(0.0)

    # Output
    full_text = args.separator.join(all_texts)

    # Determine output path: --output or auto-generate next to PDF
    if args.output:
        out_path = args.output
    else:
        out_path = args.pdf.with_suffix(".txt")

    out_path.write_text(full_text, encoding="utf-8")
    print(f"\nSaved to: {out_path}")

    # Also print to console
    print("\n" + "=" * 60)
    print("EXTRACTED TEXT")
    print("=" * 60)
    if args.confidence:
        for i, (txt, conf) in enumerate(zip(all_texts, all_confs), 1):
            print(f"\n--- Page {i} [{conf:.2%}] ---")
            print(txt)
    else:
        print(full_text)
    print("=" * 60)

    # Summary
    valid_confs = [c for c in all_confs if c > 0]
    if valid_confs:
        avg = sum(valid_confs) / len(valid_confs)
        print(f"\nPages processed: {len(valid_confs)}/{len(pages)}")
        print(f"Overall confidence: {avg:.2%}")
        print(f"Total characters: {len(full_text)}")


if __name__ == "__main__":
    main()
