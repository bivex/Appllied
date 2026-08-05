# ADR-0001: Adopt Hexagonal (Ports & Adapters) Architecture

* **Status:** Accepted
* **Deciders:** Architecture Governance Team, Lead Systems Architect
* **Date:** 2026-08-05
* **ISO 42010 Clause Alignment:** §6.1 Architecture Viewpoints & §7 Architectural Rationale

## Context and Problem Statement

Optical Character Recognition (OCR) applications frequently bind domain models directly to specific third-party engines (e.g., Tesseract, EasyOCR, or Cloud OCR APIs). Tight coupling makes switching or augmenting OCR hardware engines difficult, degrades testability, and leaks OS/framework specifics into core business rules.

How should we structure the Appllied system to ensure domain independence and engine pluggability?

## Decision Drivers

* High testability: Core domain rules (e.g. document hierarchy, structure extraction, bounding box calculations) must be testable without native hardware APIs or GUI dependencies.
* Engine interchangeability: System must support Apple Vision framework on macOS, custom CoreML/ANE models, or synthetic test stubs without modifying application code.
* ISO 25010 maintainability and testability compliance.

## Considered Options

1. **Option 1: Monolithic / Layered Architecture** with direct PyObjC imports in business logic.
2. **Option 2: Hexagonal (Ports & Adapters) Architecture** combined with Domain-Driven Design (DDD).
3. **Option 3: Microservice Architecture** splitting engine and processing into independent network services.

## Decision Outcome

**Chosen Option:** **Option 2 (Hexagonal Architecture)**.

### Architectural Structure:
- **Domain Layer (`ocr_system/domain/`)**: Pure Python entities (`Document`, `TextLine`, `Word`, `Character`), value objects (`BoundingBox`), and domain events. Zero external dependencies.
- **Application Layer (`ocr_system/application/`)**: Use cases (`ProcessDocumentUseCase`, `ExtractStructureUseCase`) and abstract Ports (`OCREngine`, `ImageSource`, `DocumentRepository`).
- **Infrastructure Layer (`ocr_system/infrastructure/`)**: Concrete Adapters (`VisionOCRAdapter`, `CustomModelOCRAdapter`, `LocalFileImageSource`, `InMemoryDocumentRepository`).

### Consequences

* **Positive:**
  - Fast, isolated unit testing (20+ tests run in <0.05 seconds without OS engine calls).
  - Ability to substitute OCR hardware engines dynamically via DI Container (`ocr_system/container.py`).
  - Strict compliance with ISO 42010 functional viewpoint framing.
* **Negative:**
  - Additional abstraction boilerplate (abstract interface classes, DTOs, and mapping layers).
