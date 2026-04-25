#!/usr/bin/env python3
"""
PDF rendering utilities using Quartz.

Renders PDF pages to CGImage objects and queries page metadata.
"""

from __future__ import annotations

from typing import Optional

from ocr_system.infrastructure.constants import (
    PDF_FALLBACK_PAGE_COUNT,
    PDF_RENDER_SCALE_DEFAULT,
    QUARTZ_BITMAP_INFO_PREMULTIPLIED_FIRST_LITTLE_ENDIAN,
    QUARTZ_BITS_PER_COMPONENT,
    QUARTZ_BYTES_PER_ROW_AUTO,
    QUARTZ_WHITE_FILL,
)

# Check Vision/Quartz availability
try:
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
        CGImageSourceCreateWithURL,
        CGImageSourceGetCount,
    )
    from Quartz import (
        CGRectMake,
        CGContextConcatCTM,
        CGAffineTransformMakeScale,
    )
    VISION_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import required frameworks: {e}")
    VISION_AVAILABLE = False


def render_pdf_page_to_cgimage(pdf_url, page_num: int, scale: float = PDF_RENDER_SCALE_DEFAULT):
    """
    Render a single PDF page to CGImage.

    Args:
        pdf_url: NSURL to PDF file
        page_num: 1-based page number
        scale: Scale factor for rendering (2.0 = 2x resolution)

    Returns:
        CGImage object or None
    """
    pdf = CGPDFDocumentCreateWithURL(pdf_url)
    if pdf is None:
        print("  Error: Could not open PDF")
        return None

    page = CGPDFDocumentGetPage(pdf, page_num)
    if page is None:
        print(f"  Error: Could not get page {page_num}")
        return None

    rect = CGPDFPageGetBoxRect(page, kCGPDFMediaBox)
    width = int(rect.size.width * scale)
    height = int(rect.size.height * scale)

    if width <= 0 or height <= 0:
        print(f"  Error: Invalid dimensions {width}x{height}")
        return None

    print(f"  Rendering at {width}x{height} (scale {scale}x)")

    color_space = CGColorSpaceCreateDeviceRGB()
    context = CGBitmapContextCreate(
        None,
        width,
        height,
        QUARTZ_BITS_PER_COMPONENT,
        QUARTZ_BYTES_PER_ROW_AUTO,
        color_space,
        QUARTZ_BITMAP_INFO_PREMULTIPLIED_FIRST_LITTLE_ENDIAN,
    )

    if context is None:
        print("  Error: Could not create bitmap context")
        return None

    full_rect = CGRectMake(0, 0, width, height)
    CGContextSetRGBFillColor(context, *QUARTZ_WHITE_FILL)
    CGContextFillRect(context, full_rect)

    transform = CGAffineTransformMakeScale(scale, scale)
    CGContextConcatCTM(context, transform)
    CGContextDrawPDFPage(context, page)

    return CGBitmapContextCreateImage(context)


def get_page_count(pdf_url) -> int:
    """Get total page count from PDF, with fallback."""
    source = CGImageSourceCreateWithURL(pdf_url, None)
    if source:
        total = CGImageSourceGetCount(source)
        print(f"PDF: {total} page(s)")
        return total
    print("Warning: Could not get page count via CGImageSource")
    return PDF_FALLBACK_PAGE_COUNT
