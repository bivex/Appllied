"""
Example: Using the OCR System with a local image.

This script demonstrates how to process an image file using the OCR system.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to allow imports when running as script
sys.path.insert(0, str(Path(__file__).parent))

from ocr_system.container import OCRContainer
from ocr_system.domain import DocumentType


async def main():
    # Initialize container with default (Vision) adapter
    container = OCRContainer()

    # Get the process document use case
    process = container.create_process_document_use_case()

    # Process an image (replace with your image path)
    image_path = "sample.png"
    if len(sys.argv) > 1:
        image_path = sys.argv[1]

    if not Path(image_path).exists():
        print(f"Image not found: {image_path}")
        print("Usage: python examples/basic_usage.py [image_path]")
        return

    print(f"Processing {image_path}...")
    document = await process.execute(
        image_url=image_path, document_type=DocumentType.GENERIC
    )

    # Output results
    print("\n" + "=" * 60)
    print("OCR RESULTS")
    print("=" * 60)
    print(f"Document ID: {document.id}")
    print(f"Processed at: {document.processed_at}")
    print(f"Number of lines: {len(document.lines)}")
    print(
        f"Average confidence: {sum(l.confidence for l in document.lines) / len(document.lines):.2%}"
    )
    print("\nFull text:")
    print("-" * 60)
    print(document.get_full_text())
    print("\nStructured elements:")
    print(f"  Paragraphs: {len(document.paragraphs)}")
    print(f"  Tables: {len(document.tables)}")
    entities = document.extract_entities()
    if entities:
        print(f"  Entities:")
        for e in entities:
            print(f"    - {e.entity_type.value}: {e.value} (conf: {e.confidence:.2%})")


if __name__ == "__main__":
    asyncio.run(main())
