"""Image utility functions for OCR preprocessing."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional


def fix_transparent_background(
    image_path: Path, output_path: Optional[Path] = None
) -> Path:
    """
    Composite an RGBA image onto a white background to avoid Vision's
    transparent->black interpretation issue.

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
        sys.exit(1)

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
