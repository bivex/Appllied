# Quick Start Guide

## Installation

```bash
# Clone and install
git clone <your-repo>
cd ocr_system
pip install -e .

# Or install dependencies manually
pip install -r requirements.txt
```

## Generate Test Images

```bash
# Basic: create 5 random text images
python -m ocr_system.scripts.generate_text_images

# After install, you can also use:
ocr-generate --num 10 --output-dir ./data/test

# Create an image with specific text
python -m ocr_system.scripts.generate_text_images --text "Hello Vision OCR" --font-size 64
```

This creates PNG files in `generated_images/` (or specified directory).

## Extract Text (macOS only)

```bash
# Extract text using Vision (requires macOS + PyObjC)
python -m ocr_system.scripts.extract_text generated_images/sample_001.png

# Use fast mode (less accurate but quicker)
python -m ocr_system.scripts.extract_text image.png --level fast

# Use handwriting-optimized mode (iOS 16+/macOS 13+)
python -m ocr_system.scripts.extract_text drawing.png --handwriting

# Save output to file
python -m ocr_system.scripts.extract_text image.png --output text.txt

# Show confidence
python -m ocr_system.scripts.extract_text image.png --confidence
```

**Important**: PencilKit drawings have transparent backgrounds. Vision interprets transparency as black, so black strokes become invisible. The script auto-fixes this by compositing onto white. To disable:

```bash
python -m ocr_system.scripts.extract_text image.png --no-fix-bg
```

## Use in Python Code

```python
import asyncio
from ocr_system.container import OCRContainer
from ocr_system.domain import DocumentType

async def ocr(image_path: str):
    container = OCRContainer()
    process = container.create_process_document_use_case()

    document = await process.execute(
        image_url=image_path,
        document_type=DocumentType.GENERIC
    )

    print(f"Text: {document.get_full_text()}")
    print(f"Lines: {len(document.lines)}")
    print(f"Paragraphs: {len(document.paragraphs)}")
    return document

asyncio.run(ocr("sample.png"))
```

## Troubleshooting

### "Vision framework not available"

Install PyObjC:

```bash
pip install pyobjc-framework-Vision pyobjc-framework-CoreML
```

Or use the bundled mock adapter (for development/testing):

```python
from ocr_system.infrastructure import CustomModelOCRAdapter
container = OCRContainer(use_custom_model=True, model_path="path/to/model.mlmodel")
```

### "No text recognized" from PencilKit

The drawing likely has a transparent background. The CLI tool auto-fixes this. If using code directly:

```swift
// Swift: Composite onto white before Vision
let renderer = UIGraphicsImageRenderer(size: drawing.bounds.size)
let image = renderer.image { ctx in
    UIColor.white.setFill()
    ctx.fill(drawing.bounds)
    drawing.draw(in: drawing.bounds)
}
```

See [docs/PENCILKIT_VISION_FIX.md](docs/PENCILKIT_VISION_FIX.md) for details.

### Font not found on Linux

The image generator falls back to a bitmap font if no TrueType font is found. Install fonts:

```bash
# Ubuntu/Debian
sudo apt-get install fonts-dejavu-core

# Or specify a font
python -m ocr_system.scripts.generate_text_images --font /path/to/font.ttf
```

### Mypy/type errors

Some Vision imports are platform-specific. Mypy configuration in `pyproject.toml` ignores infrastructure errors:

```toml
[[tool.mypy.overrides]]
module = "ocr_system.infrastructure.*"
ignore_errors = true
```

## Project Structure Recap

```
ocr_system/
├── domain/              # Business logic (pure Python)
├── application/         # Use cases & ports
├── infrastructure/      # Vision, CoreML, repos, sources
├── container.py         # Dependency injection
├── scripts/             # CLI tools
│   ├── generate_text_images.py
│   └── extract_text.py
├── examples/            # Usage examples
├── tests/               # Unit tests
└── docs/                # Documentation
```

## Next Steps

- Build a FastAPI/Starlette API layer: `python -m ocr_system.api`
- Add PostgreSQL repository with SQLAlchemy
- Integrate real Core ML models (handwritten digit, custom OCR)
- Set up CI/CD with GitHub Actions (run tests on commit)
