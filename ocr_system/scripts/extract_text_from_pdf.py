#!/usr/bin/env python3
"""
Extract text from PDF files using Apple Vision framework (simplified version).

Renders PDF pages to images using Quartz and runs Vision OCR.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Tuple

from ocr_system.infrastructure.constants import (
    OUTPUT_SEPARATOR_WIDTH,
    PDF_RENDER_SCALE_DEFAULT,
)

# Import PDF rendering and Vision OCR helpers
from ocr_system.scripts.pdf_renderer import (
    VISION_AVAILABLE as PDF_RENDERER_AVAILABLE,
    render_pdf_page_to_cgimage,
    get_page_count,
)
from ocr_system.scripts.vision_ocr import (
    VISION_AVAILABLE as VISION_OCR_AVAILABLE,
    recognize_text_from_cgimage,
)

# Check Vision availability (kept for backward compatibility)
try:
    import Vision
    import CoreML
    from Foundation import NSURL
    VISION_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import required frameworks: {e}")
    VISION_AVAILABLE = False


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


def resolve_pages(args) -> List[int]:
    """Determine which pages to process from CLI arguments."""
    if args.pages:
        if args.pages.lower() == "all":
            return None
        try:
            return parse_page_range(args.pages)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)
    return None


def process_page(pdf_url, page_num: int, total: int, args, revision) -> Tuple[str, float]:
    """Render and OCR a single page, returning (text, confidence)."""
    print(f"\nPage {page_num}/{total}...", flush=True)
    cg_img = render_pdf_page_to_cgimage(pdf_url, page_num, scale=args.scale)
    if cg_img is None:
        print(f"  Failed to render page {page_num}")
        return f"[Error: page {page_num} could not be rendered]", 0.0

    print("  Running Vision OCR...", flush=True)
    try:
        texts, conf = recognize_text_from_cgimage(
            cg_img,
            recognition_level=args.level,
            languages=[lang.strip() for lang in args.languages.split(",")],
            use_language_correction=not args.no_correction,
            revision=revision,
        )
        print(f"  {len(texts)} lines, avg conf: {conf:.2%}")
        return "\n".join(texts), conf
    except Exception as e:
        print(f"  OCR failed: {e}")
        return f"[Error: OCR failed on page {page_num}]", 0.0


def write_output(args, all_texts: List[str], all_confs: List[float]) -> None:
    """Write results to file and console."""
    full_text = args.separator.join(all_texts)
    out_path = args.output or args.pdf.with_suffix(".txt")
    out_path.write_text(full_text, encoding="utf-8")
    print(f"\nSaved to: {out_path}")

    separator = "=" * OUTPUT_SEPARATOR_WIDTH
    print(f"\n{separator}")
    print("EXTRACTED TEXT")
    print(separator)
    if args.confidence:
        for i, (txt, conf) in enumerate(zip(all_texts, all_confs), 1):
            print(f"\n--- Page {i} [{conf:.2%}] ---")
            print(txt)
    else:
        print(full_text)
    print(separator)

    valid_confs = [c for c in all_confs if c > 0]
    if valid_confs:
        avg = sum(valid_confs) / len(valid_confs)
        print(f"\nPages processed: {len(valid_confs)}/{len(all_texts)}")
        print(f"Overall confidence: {avg:.2%}")
        print(f"Total characters: {len(full_text)}")


def _build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for PDF extraction."""
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
    parser.add_argument("--scale", type=float, default=PDF_RENDER_SCALE_DEFAULT,
                        help=f"Render scale factor (default: {PDF_RENDER_SCALE_DEFAULT})")
    return parser


def _get_handwriting_revision(args):
    """Get handwriting revision if requested."""
    if not args.handwriting:
        return None
    try:
        return Vision.VNRecognizeTextRequestRevision3
    except AttributeError:
        print("Warning: Revision 3 not available (requires macOS 13+)")
        return None


def _resolve_page_list(page_range, total_pages):
    """Determine the final list of page numbers to process."""
    if page_range is None:
        return list(range(1, total_pages + 1))
    return [p for p in page_range if 1 <= p <= total_pages]


def main():
    args = _build_parser().parse_args()

    if not VISION_AVAILABLE:
        print("\nERROR: Vision/Quartz not available.")
        print("Install: pip install pyobjc-framework-Vision pyobjc-framework-CoreML")
        print("Requires macOS.")
        sys.exit(1)

    if not args.pdf.exists():
        print(f"Error: PDF not found: {args.pdf}")
        sys.exit(1)

    page_range = resolve_pages(args)
    revision = _get_handwriting_revision(args)

    pdf_url = NSURL.fileURLWithPath_(str(args.pdf.absolute()))
    total_pages = get_page_count(pdf_url)

    pages = _resolve_page_list(page_range, total_pages)
    print(f"Will process pages: {pages}")
    print(f"Render scale: {args.scale}x")

    all_texts, all_confs = [], []
    for p in pages:
        text, conf = process_page(pdf_url, p, len(pages), args, revision)
        all_texts.append(text)
        all_confs.append(conf)

    write_output(args, all_texts, all_confs)


if __name__ == "__main__":
    main()
