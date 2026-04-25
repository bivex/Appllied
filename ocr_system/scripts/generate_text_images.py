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
from pathlib import Path
from typing import Tuple, Optional

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Error: PIL/Pillow is required. Install with: pip install Pillow")
    exit(1)


def random_text(length: int = 10) -> str:
    """Generate random alphanumeric text."""
    chars = string.ascii_letters + string.digits + " "
    return "".join(random.choice(chars) for _ in range(length))


def random_sentence() -> str:
    """Generate a random sentence-like string."""
    words = []
    for _ in range(random.randint(3, 8)):
        words.append(random_text(random.randint(3, 8)))
    return " ".join(words).capitalize() + "."


def create_text_image(
    text: str,
    output_path: Path,
    width: int = 800,
    height: int = 200,
    font_size: int = 32,
    font_path: Optional[str] = None,
    background_color: Tuple[int, int, int] = (255, 255, 255),
    text_color: Tuple[int, int, int] = (0, 0, 0),
    padding: int = 20,
    line_spacing: int = 10,
) -> Path:
    """
    Create an image with the given text.

    Args:
        text: Text to render (can contain \n for multiple lines)
        output_path: Where to save the PNG
        width: Image width in pixels
        height: Image height in pixels
        font_size: Font size in points
        font_path: Path to .ttf/.otf font file (uses default if None)
        background_color: RGB tuple
        text_color: RGB tuple
        padding: Padding around text in pixels
        line_spacing: Extra spacing between lines

    Returns:
        Path to saved image
    """
    # Create image
    img = Image.new("RGB", (width, height), color=background_color)
    draw = ImageDraw.Draw(img)

    # Load font
    if font_path:
        try:
            font = ImageFont.truetype(font_path, font_size)
        except OSError:
            print(f"Warning: Could not load font '{font_path}', using default")
            font = ImageFont.load_default()
    else:
        # Try to load a decent system font
        possible_fonts = [
            "/System/Library/Fonts/Helvetica.ttc",  # macOS
            "/System/Library/Fonts/Arial.ttf",  # macOS
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
            "/usr/share/fonts/TTF/DejaVuSans.ttf",  # Linux alt
            "arial.ttf",  # Windows fallback
        ]
        font = None
        for fp in possible_fonts:
            if Path(fp).exists():
                try:
                    font = ImageFont.truetype(fp, font_size)
                    break
                except Exception:
                    continue
        if font is None:
            print("Warning: No TrueType font found, using bitmap font (low quality)")
            font = ImageFont.load_default()

    # Calculate text size and position
    lines = text.split("\n")
    line_heights = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_heights.append(bbox[3] - bbox[1])

    total_text_height = sum(line_heights) + line_spacing * (len(lines) - 1)
    y = padding + (height - total_text_height - 2 * padding) // 2

    # Draw each line
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = padding + (width - 2 * padding - text_width) // 2

        draw.text((x, y), line, fill=text_color, font=font)
        y += line_heights[i] + line_spacing

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    print(f"Saved: {output_path} ({width}x{height}, {len(text)} chars)")
    return output_path


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

    # Vary parameters across samples
    backgrounds = [
        (255, 255, 255),  # white
        (240, 240, 240),  # light gray
        (255, 250, 240),  # cream
    ]
    text_colors = [
        (0, 0, 0),  # black
        (50, 50, 50),  # dark gray
        (100, 100, 100),  # gray
    ]

    for i in range(1, num_images + 1):
        # Randomize content
        if random.random() < 0.5:
            text = random_sentence()
        else:
            # Multi-line
            lines = [random_sentence() for _ in range(random.randint(2, 5))]
            text = "\n".join(lines)

        # Randomize appearance
        width = random.choice([800, 1200])
        height = random.choice([200, 300, 400])
        font_size = random.choice([24, 32, 48])
        bg = random.choice(backgrounds)
        fg = random.choice(text_colors)

        filename = f"{base_name}_{i:03d}.png"
        output_path = output_dir / filename

        create_text_image(
            text=text,
            output_path=output_path,
            width=width,
            height=height,
            font_size=font_size,
            background_color=bg,
            text_color=fg,
        )

    print(f"\nGenerated {num_images} images in {output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate random text images for OCR testing"
    )
    parser.add_argument(
        "-n",
        "--num",
        type=int,
        default=5,
        help="Number of images to generate (default: 5)",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("generated_images"),
        help="Output directory (default: generated_images)",
    )
    parser.add_argument(
        "--text",
        type=str,
        default=None,
        help="Specific text to render (single image, ignores --num)",
    )
    parser.add_argument(
        "--width", type=int, default=800, help="Image width (default: 800)"
    )
    parser.add_argument(
        "--height", type=int, default=200, help="Image height (default: 200)"
    )
    parser.add_argument(
        "--font-size", type=int, default=32, help="Font size (default: 32)"
    )
    parser.add_argument(
        "--font", type=Path, default=None, help="Path to TTF/OTF font file"
    )
    parser.add_argument(
        "--bg-color",
        type=str,
        default="white",
        help="Background color (name or R,G,B e.g. 'white' or '255,255,255')",
    )
    parser.add_argument(
        "--text-color", type=str, default="black", help="Text color (name or R,G,B)"
    )

    args = parser.parse_args()

    # Parse colors
    def parse_color(s: str) -> Tuple[int, int, int]:
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
        # Parse R,G,B
        try:
            r, g, b = map(int, s.split(","))
            return (r, g, b)
        except Exception:
            raise ValueError(f"Invalid color: {s}")

    try:
        bg_color = parse_color(args.bg_color)
        text_color = parse_color(args.text_color)
    except ValueError as e:
        print(f"Error: {e}")
        exit(1)

    # Generate
    if args.text:
        # Single image with specific text
        output_path = args.output_dir / "custom.png"
        create_text_image(
            text=args.text,
            output_path=output_path,
            width=args.width,
            height=args.height,
            font_size=args.font_size,
            font_path=args.font,
            background_color=bg_color,
            text_color=text_color,
        )
    else:
        # Dataset generation
        generate_dataset(
            output_dir=args.output_dir,
            num_images=args.num,
            base_name="sample",
        )


if __name__ == "__main__":
    main()
