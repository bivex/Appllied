# Applied Engineering Projects

A collection of software engineering projects demonstrating Domain-Driven Design, clean architecture, and modern best practices.

## Projects

### 🔤 OCR System (`ocr_system/`)

A complete optical character recognition system implementing Apple's Vision framework design patterns.

**Key Features:**
- Two-path OCR: fast (character-level) vs accurate (line/sentence with language correction)
- Domain-Driven Design with hexagonal architecture
- Vision framework integration (macOS/iOS) with PencilKit support
- ANE-optimized Core ML model adapter
- CLI tools for generating test data and extracting text
- Comprehensive unit tests and end-to-end tests

**Tech Stack:**
- Python 3.9+ with async/await
- PyObjC (Vision, CoreML, Quartz)
- Pillow (image generation)
- pytest (testing)

**Quick Start:**
```bash
# Install dependencies
pip install -e .

# Generate test images
ocr-generate --num 5

# Extract text (macOS only)
ocr-extract generated_images/sample_001.png --confidence
```

**Architecture:**
```
domain/        # Pure business logic (entities, value objects, aggregates)
application/   # Use cases, ports (interfaces), services
infrastructure/# Adapters: Vision, CoreML, repositories, sources
scripts/       # CLI tools: generate_text_images, extract_text
tests/         # Unit tests (20 passing)
```

**Documentation:**
- [OCR System README](ocr_system/README.md) — Full architecture guide
- [Quick Start](ocr_system/docs/QUICKSTART.md) — Get started in minutes
- [PencilKit Vision Fix](ocr_system/docs/PENCILKIT_VISION_FIX.md) — Transparent background solution
- [Implementation Summary](ocr_system/IMPLEMENTATION_SUMMARY.md) — Technical deep dive

**Git History:**
```
dca6bbd docs: add implementation summary and test results
b7c7cd0 test: add end-to-end test script for CLI tools
36cfa9f test: fix import paths and character cache test assertion
3d283af docs: add scripts summary and quick reference
fa60d17 feat: add CLI tools for text image generation and Vision extraction
129b81c feat: implement OCR system with DDD and hexagonal architecture
```

---

## Development Philosophy

All projects in this repository follow these principles:

- **Domain-Driven Design**: Rich domain models, ubiquitous language, aggregates
- **Clean/Hexagonal Architecture**: Clear layer separation, ports & adapters
- **SOLID Principles**: Single responsibility, dependency inversion, interface segregation
- **Testability**: High test coverage, dependency injection, mocking-friendly
- **Documentation**: Comprehensive docs, ADRs, inline comments where needed
- **Type Safety**: Type hints throughout, mypy strict mode where possible

## Requirements

Each project may have specific requirements. See project READMEs for details.

Generally:
- Python 3.9+
- Dependencies listed in `requirements.txt` or `pyproject.toml`
- Optional: virtual environment (recommended)

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=<project_name>

# End-to-end tests (if available)
bash scripts/test_e2e.sh
```

## Contributing

These are personal learning/experimentation projects. Feel free to fork, study, and adapt.

## License

MIT — see individual project directories for details.

---

**Status**: Actively developed. Check individual project READMEs for roadmaps.
