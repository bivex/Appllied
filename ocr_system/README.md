# OCR System

A modern OCR system implementing Domain-Driven Design (DDD) and Hexagonal Architecture (Ports & Adapters), inspired by Apple's Vision framework design principles.

## Architecture Overview

```
├── domain/           # Core business logic, pure Python, no dependencies
│   ├── entities     # TextLine, Word, Character, Document, Paragraph, Table
│   ├── value_objects # BoundingBox, Point, Polygon, Language
│   ├── aggregates   # Document, OCRAggregate
│   └── events       # Domain events (OCRRequested, OCRCompleted, etc.)
├── application/     # Use cases and application services
│   ├── use_cases   # ProcessDocument, GetDocument, SearchDocuments
│   ├── services    # PathSelectionStrategy, LanguageCorrectionService
│   └── ports       # Repository, ImageSource, OCREngine interfaces
├── infrastructure/  # External adapters
│   ├── vision.py   # Apple Vision framework adapter (macOS/iOS)
│   ├── custom_model.py # ANE-optimized custom model adapter
│   ├── repositories.py # In-memory / database repositories
│   └── sources.py  # Local file and HTTP image sources
├── container.py    # Dependency injection composition root
└── tests/          # Unit and integration tests
```

## Key Design Decisions

### 1. Two-Path OCR Strategy
Following Apple's Vision, the system supports two recognition paths:

- **FAST**: Character-level recognition using lightweight models (like `VNDetectTextRectanglesRequest`)
- **ACCURATE**: Deep learning model that recognizes full lines and sentences with language correction

### 2. Domain Model

The domain layer defines core concepts:

- **BoundingBox**: Immutable value object with geometry and confidence
- **TextLine → Word → Character**: Hierarchy of recognized text elements
- **Document**: Aggregate root that owns lines and derived structure
- **Paragraph/Table/Entity**: Structured extraction results

### 3. Hexagonal Architecture

All external dependencies are injected via ports (interfaces):

- `OCREngine` port implemented by `VisionOCRAdapter` or `CustomModelOCRAdapter`
- `ImageSource` port implemented by `LocalFileImageSource` or `HttpImageSource`
- `DocumentRepository` port implemented by `InMemoryDocumentRepository` or SQLAlchemy implementation

### 4. Use-Case Driven

Application layer orchestrates workflows:

1. `ProcessDocumentUseCase`: Main OCR workflow
   - Retrieve image
   - Select processing path (fast vs accurate)
   - Recognize text
   - Apply language correction
   - Extract structure (paragraphs, tables, entities)
   - Persist result

2. `ExtractStructureUseCase`: Separate structure extraction
3. `GetDocumentUseCase`: Retrieve by ID
4. `SearchDocumentsUseCase`: Search by type/content

### 5. Domain Events

Aggregates emit events for side effects:

- `OCRRequested`
- `OCREngineSelected`
- `TextRecognized`
- `LanguageCorrected`
- `OCRCompleted`

These enable logging, metrics, and asynchronous handling.

### 6. Language Correction

Separate domain service applies language-specific rules to improve OCR accuracy, similar to Vision's `usesLanguageCorrection`.

### 7. Structured Document Extraction

Beyond plain text, the system can recognize:

- Paragraphs (grouping lines by vertical proximity)
- Tables (detecting grid structure)
- Entities (emails, URLs, phone numbers via regex)

### 8. ANE Optimization

Custom model adapter demonstrates ANE-friendly design:

- Uses `CoreML` with `.all` compute units (CPU + GPU + ANE)
- Recommends replacing `Linear` layers with `Conv2d 1x1` for ANE efficiency
- Supports model quantization for edge deployment

## Getting Started

### Prerequisites

- Python 3.9+
- (Optional for Vision) macOS/iOS with PyObjC (`pip install pyobjc`)
- (Optional for HTTP) aiohttp (`pip install aiohttp`)

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

### Basic Usage

```python
import asyncio
from container import OCRContainer
from domain import DocumentType

async def main():
    # Initialize container with Vision OCR
    container = OCRContainer(use_vision=True)
    
    # Get use case
    process = container.create_process_document_use_case()
    
    # Process an image
    document = await process.execute(
        image_url="path/to/document.png",
        document_type=DocumentType.GENERIC
    )
    
    print(f"Text: {document.get_full_text()}")
    print(f"Paragraphs: {len(document.paragraphs)}")
    print(f"Entities found: {len(document.extract_entities())}")

asyncio.run(main())
```

### Configuration

Environment variables:

- `OCR_DEFAULT_PATH`: `fast` or `accurate` (default: accurate)
- `OCR_USE_CORRECTION`: `true` or `false` (default: true)
- `OCR_TEMP_DIR`: temporary directory (default: /tmp/ocr)
- `OCR_MAX_IMAGE_SIZE_MB`: max image size in MB (default: 20)

Or programmatic config:

```python
from infrastructure import OCRConfig

config = OCRConfig(
    default_path=OCRPath.ACCURATE,
    use_language_correction=True,
    temp_directory="./tmp"
)
container = OCRContainer(config=config)
```

### Custom Model

```python
container = OCRContainer(
    use_custom_model=True,
    model_path="/path/to/model.mlmodel"
)
```

## Testing

```bash
# Run unit tests
pytest tests/

# Run with coverage
pytest --cov=ocr_system tests/
```

## Project Structure Explanation

### Domain Layer
- **Pure Python**, no external dependencies.
- Contains all business rules and invariants.
- Entities enforce their own consistency (e.g., TextLine confidence is immutable after creation? Not enforced but can be).
- Value objects are immutable (`@dataclass(frozen=True)`).
- Aggregates manage lifecycle and consistency boundaries.
- Domain events capture things that happened.

### Application Layer
- **Use cases** represent single, cohesive pieces of functionality.
- **Ports** (interfaces) define what the application needs from the outside world.
- **Services** contain domain logic that doesn't naturally belong to an entity.
- No direct dependencies on frameworks; only on domain and ports.

### Infrastructure Layer
- **Adapters** implement ports defined in application.
- Vision adapter uses Apple's Vision via PyObjC.
- Custom model adapter shows ANE-optimized patterns (1x1 convs, etc.).
- Repositories handle persistence (in-memory currently).
- Sources handle external IO (filesystem, HTTP).

### Composition Root
- Single place where dependencies are wired together.
- Configures which implementations to use.
- Can be replaced with a proper DI container if needed.

## Clean Architecture Principles Applied

1. **Independence of Frameworks**: Domain and application don't depend on Vision, aiohttp, SQLAlchemy, etc.
2. **Testability**: All dependencies are interfaces, easily mocked.
3. **Plug-and-Play**: Swapping Vision for Tesseract or a custom model requires only new adapter.
4. **UI Independence**: Presentation layer (CLI/API) can be added without affecting core.
5. **Database Independence**: Repository pattern allows any storage backend.

## Future Enhancements

- [ ] Real Vision integration with image preprocessing (CGImage conversion, orientation)
- [ ] TensorFlow/PyTorch model adapter for ONNX conversion to Core ML
- [ ] Async processing queue for batch documents
- [ ] API layer (FastAPI) exposing OCR as a service
- [ ] PostgreSQL repository with full-text search
- [ ]CQRS: separate read models for search
- [ ] Event sourcing: store domain events for audit trail
- [ ] Distributed tracing and metrics (OpenTelemetry)
- [ ] Graceful degradation: fallback to Tesseract if Vision unavailable

## License

MIT
