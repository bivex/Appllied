# Added CLI Scripts — Summary

## Commits

### 1. 129b81c — feat: implement OCR system with DDD and hexagonal architecture
Initial implementation with:
- Domain layer (entities, value objects, aggregates, events)
- Application layer (use cases, ports, services)
- Infrastructure layer (Vision, CoreML adapters)
- Dependency injection container
- Unit tests

### 2. fa60d17 — feat: add CLI tools for text image generation and Vision extraction
Added two command-line utilities:

#### `scripts/generate_text_images.py` → `ocr-generate`
Generates PNG images with random text for OCR testing.

Features:
- Custom or random text (sentences, multi-line)
- Configurable dimensions, font size, colors
- Auto-detects system fonts (Helvetica, Arial, DejaVuSans)
- Batch mode: generate N images with variations
- Colors as names or R,G,B tuples

Examples:
```bash
# 10 random images
ocr-generate --num 10 --output-dir ./data/train

# Single image with specific text
ocr-generate --text "Hello World" --font-size 64 --bg-color white --text-color black

# Multi-line
ocr-generate --text "Line1\nLine2\nLine3" --height 400
```

#### `scripts/extract_text.py` → `ocr-extract`
Extracts text from images using Apple Vision framework.

Features:
- Fast/accurate recognition levels
- Handwriting-optimized mode (iOS 16+ revision 3)
- Multi-language support (BCP-47 codes)
- Automatic transparent background fix (PencilKit)
- Confidence scores
- Save to file

Examples:
```bash
# Basic extraction
ocr-extract image.png

# Fast mode
ocr-extract image.png --level fast

# Handwriting with confidence
ocr-extract drawing.png --handwriting --confidence

# Save output
ocr-extract image.png --output text.txt

# Multiple languages
ocr-extract image.png --languages en-US,fr-FR

# Disable auto-fix (for images with proper white background already)
ocr-extract image.png --no-fix-bg
```

#### Critical Fix: Transparent Background

**Problem**: PencilKit drawings (PKCanvasView) render with transparent backgrounds. Vision interprets transparent pixels as black, so black strokes on "black" = invisible → "No text recognized".

**Solution**: The script automatically composites the image onto a white background using PIL/Pillow before Vision processing.

```python
# Detect RGBA/LA modes
if image.mode in ("RGBA", "LA", "P"):
    background = Image.new("RGB", image.size, (255, 255, 255))
    background.paste(image, mask=image.split()[-1])
```

See: `docs/PENCILKIT_VISION_FIX.md` for full explanation.

## Updated Files

- `requirements.txt`: Added Pillow dependency
- `pyproject.toml`: Added `[project.scripts]` entry points for `ocr-generate` and `ocr-extract`
- `README.md`: Added "CLI Tools" section with usage
- `docs/QUICKSTART.md`: New guide with install, examples, troubleshooting
- `docs/__init__.py`: Package init

## Usage After Installation

```bash
# Install
pip install -e .

# Now available as commands anywhere:
ocr-generate --help
ocr-extract --help
```

## Files Added (fa60d17)

```
docs/QUICKSTART.md                                    | 155 ++++++
docs/__init__.py                                      |   1 +
scripts/__init__.py                                   |   1 +
scripts/extract_text.py                               | 354 ++++++++++
scripts/generate_text_images.py                       | 285 ++++++++
```

Total: 900 insertions across 8 files modified/created.
