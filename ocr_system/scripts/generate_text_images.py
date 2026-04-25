#!/usr/bin/env python3
"""
Generate random text images for OCR testing.

Creates PNG images with random text in various fonts, sizes, and layouts.
Useful for testing OCR systems like Vision or custom models.
"""

from __future__ import annotations

import argparse
import random
import string
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple, Optional

from ocr_system.infrastructure.constants import (
    BACKGROUND_PALETTE,
    DEFAULT_IMAGE_PADDING,
    DEFAULT_LINE_SPACING,
    DEFAULT_TEXT_LENGTH,
    FONT_SIZE_CANDIDATES,
    IMAGE_HEIGHT_CANDIDATES,
    IMAGE_WIDTH_CANDIDATES,
    MULTILINE_COUNT_MAX,
    MULTILINE_COUNT_MIN,
    MULTILINE_PROBABILITY,
    RANDOM_WORD_COUNT_MAX,
    RANDOM_WORD_COUNT_MIN,
    RANDOM_WORD_LENGTH_MAX,
    RANDOM_WORD_LENGTH_MIN,
    SYSTEM_FONT_PATHS,
    TEXT_COLOR_PALETTE,
)

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Error: PIL/Pillow is required. Install with: pip install Pillow")
    sys.exit(1)


@dataclass
class TextImageOptions:
    """Styling options for text image generation."""

    width: int = IMAGE_WIDTH_CANDIDATES[0]
    height: int = IMAGE_HEIGHT_CANDIDATES[0]
    font_size: int = FONT_SIZE_CANDIDATES[1]
    font_path: Optional[str] = None
    background_color: Tuple[int, int, int] = BACKGROUND_PALETTE[0]
    text_color: Tuple[int, int, int] = TEXT_COLOR_PALETTE[0]
    padding: int = DEFAULT_IMAGE_PADDING
    line_spacing: int = DEFAULT_LINE_SPACING


def random_text(length: int = DEFAULT_TEXT_LENGTH) -> str:
    """Generate random alphanumeric text."""
    chars = string.ascii_letters + string.digits + " "
    return "".join(random.choice(chars) for _ in range(length))


def random_sentence() -> str:
    """Generate a random sentence-like string."""
    words = []
    for _ in range(random.randint(RANDOM_WORD_COUNT_MIN, RANDOM_WORD_COUNT_MAX)):
        words.append(random_text(random.randint(RANDOM_WORD_LENGTH_MIN, RANDOM_WORD_LENGTH_MAX)))
    return " ".join(words).capitalize() + "."


def parse_color(s: str) -> Tuple[int, int, int]:
    """Parse a color string (name or R,G,B) into an RGB tuple."""
    s = s.strip().lower()
    named = {
        "white": (255, 255, 255),
        "black": (0, 0, 0),
        "red": (255, 0, 0),
        "green": (0, 255, 0),
        "blue": (0, 0, 255),
        "gray": (128, 128, 128),
        "grey": (128, 128, 128),
    }
    if s in named:
        return named[s]
    try:
        r, g, b = map(int, s.split(","))
        return (r, g, b)
    except Exception:
        raise ValueError(f"Invalid color: {s}")


def _load_font(font_size: int, font_path: Optional[str] = None):
    """Load a font, falling back through system fonts."""
    if font_path:
        try:
            return ImageFont.truetype(font_path, font_size)
        except OSError:
            print(f"Warning: Could not load font '{font_path}', using default")
            return ImageFont.load_default()

    for fp in SYSTEM_FONT_PATHS:
        if Path(fp).exists():
            try:
                return ImageFont.truetype(fp, font_size)
            except Exception:
                continue

    print("Warning: No TrueType font found, using bitmap font (low quality)")
    return ImageFont.load_default()


def _render_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font,
    width: int,
    height: int,
    text_color: Tuple[int, int, int],
    padding: int,
    line_spacing: int,
) -> None:
    """Render text onto a PIL Draw context, centered vertically and horizontally."""
    lines = text.split("\n")
    line_heights = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_heights.append(bbox[3] - bbox[1])

    total_text_height = sum(line_heights) + line_spacing * (len(lines) - 1)
    y = padding + (height - total_text_height - 2 * padding) // 2

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = padding + (width - 2 * padding - text_width) // 2
        draw.text((x, y), line, fill=text_color, font=font)
        y += line_heights[i] + line_spacing


def create_text_image(
    text: str,
    output_path: Path,
    options: TextImageOptions = TextImageOptions(),
) -> Path:
    """
    Create an image with the given text.

    Args:
        text: Text to render (can contain \\n for multiple lines)
        output_path: Where to save the PNG
        options: Styling options (width, height, font, colors, padding, spacing)

    Returns:
        Path to saved image
    """
    img = Image.new("RGB", (options.width, options.height), color=options.background_color)
    draw = ImageDraw.Draw(img)
    font = _load_font(options.font_size, options.font_path)

    _render_text(
        draw, text, font,
        options.width, options.height,
        options.text_color, options.padding, options.line_spacing,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    print(f"Saved: {output_path} ({options.width}x{options.height}, {len(text)} chars)")
    return output_path


def _generate_random_image(
    output_dir: Path,
    index: int,
    base_name: str,
) -> None:
    """Generate a single random text image with randomised styling."""
    if random.random() < MULTILINE_PROBABILITY:
        text = random_sentence()
    else:
        lines = [random_sentence() for _ in range(
            random.randint(MULTILINE_COUNT_MIN, MULTILINE_COUNT_MAX)
        )]
        text = "\n".join(lines)

    options = TextImageOptions(
        width=random.choice(IMAGE_WIDTH_CANDIDATES),
        height=random.choice(IMAGE_HEIGHT_CANDIDATES),
        font_size=random.choice(FONT_SIZE_CANDIDATES),
        background_color=random.choice(BACKGROUND_PALETTE),
        text_color=random.choice(TEXT_COLOR_PALETTE),
    )

    filename = f"{base_name}_{index:03d}.png"
    create_text_image(text=text, output_path=output_dir / filename, options=options)


def generate_dataset(
    output_dir: Path,
    num_images: int = 10,
    base_name: str = "sample",
) -> None:
    """
    Generate a dataset of random text images with varying characteristics.

    Args:
        output_dir: Directory to save images
        num_images: Number of images to generate
        base_name: Base filename (e.g., "sample" -> sample_001.png)
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    for i in range(1, num_images + 1):
        _generate_random_image(output_dir, i, base_name)

    print(f"\nGenerated {num_images} images in {output_dir}")


def _build_default_options(args) -> TextImageOptions:
    """Construct TextImageOptions from parsed CLI arguments."""
    bg_color = parse_color(args.bg_color)
    text_color = parse_color(args.text_color)
    return TextImageOptions(
        width=args.width,
        height=args.height,
        font_size=args.font_size,
        font_path=args.font,
        background_color=bg_color,
        text_color=text_color,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Generate random text images for OCR testing"
    )
    parser.add_argument(
        "-n", "--num", type=int, default=5,
        help="Number of images to generate (default: 5)",
    )
    parser.add_argument(
        "-o", "--output-dir", type=Path, default=Path("generated_images"),
        help="Output directory (default: generated_images)",
    )
    parser.add_argument(
        "--text", type=str, default=None,
        help="Specific text to render (single image, ignores --num)",
    )
    parser.add_argument(
        "--width", type=int, default=IMAGE_WIDTH_CANDIDATES[0],
        help=f"Image width (default: {IMAGE_WIDTH_CANDIDATES[0]})",
    )
    parser.add_argument(
        "--height", type=int, default=IMAGE_HEIGHT_CANDIDATES[0],
        help=f"Image height (default: {IMAGE_HEIGHT_CANDIDATES[0]})",
    )
    parser.add_argument(
        "--font-size", type=int, default=FONT_SIZE_CANDIDATES[1],
        help=f"Font size (default: {FONT_SIZE_CANDIDATES[1]})",
    )
    parser.add_argument(
        "--font", type=Path, default=None, help="Path to TTF/OTF font file"
    )
    parser.add_argument(
        "--bg-color", type=str, default="white",
        help="Background color (name or R,G,B e.g. 'white' or '255,255,255')",
    )
    parser.add_argument(
        "--text-color", type=str, default="black",
        help="Text color (name or R,G,B)",
    )

    args = parser.parse_args()

    try:
        options = _build_default_options(args)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    if args.text:
        create_text_image(
            text=args.text,
            output_path=args.output_dir / "custom.png",
            options=options,
        )
    else:
        generate_dataset(
            output_dir=args.output_dir,
            num_images=args.num,
            base_name="sample",
        )


if __name__ == "__main__":
    main()
