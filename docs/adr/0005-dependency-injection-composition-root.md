# ADR-0005: Centralized Composition Root and Dependency Injection

* **Status:** Accepted
* **Deciders:** Lead Systems Architect, Application Developer Team
* **Date:** 2026-08-05
* **ISO 42010 Clause Alignment:** §6.1 Architecture Viewpoints & §8.1 Architecture Consistency

## Context and Problem Statement

To adhere to the Dependency Inversion Principle (DIP), application use cases (`ProcessDocumentUseCase`, `ExtractStructureUseCase`) must depend exclusively on abstract ports (`OCREngine`, `ImageSource`, `DocumentRepository`). Constructing concrete infrastructure instances inside use cases would break encapsulation and ruin testability.

Where and how should concrete infrastructure adapters be wired to application use cases?

## Decision Drivers

* Single Responsibility Principle (SRP): Decouple object graph instantiation from business logic.
* Runtime Environment Adaptability: Allow seamless switching between native macOS Vision hardware, custom model backends, or mock test repositories via environment configuration.
* Zero external framework lock-in for dependency injection (avoiding heavy DI frameworks).

## Considered Options

1. **Option 1: Hardcoded instantiation inside Use Case constructors**.
2. **Option 2: Centralized Composition Root (`ocr_system/container.py`)** with factory methods and lightweight DI Container.
3. **Option 3: External DI Framework** (e.g. `dependency_injector` or `python-inject`).

## Decision Outcome

**Chosen Option:** **Option 2 (Centralized Composition Root via `Container` class)**.

### Implementation Overview:
- `ocr_system/container.py` defines `OCRContainer`, acting as the single Composition Root.
- `OCRContainer.create_process_use_case()` encapsulates adapter selection (e.g. `VisionOCRAdapter` vs `CustomModelOCRAdapter`), repository instantiation, and strategy configuration based on `SystemConfig`.

### Consequences

* **Positive:**
  - Standardized application bootstrapping across CLI entry points, web APIs, and test suites.
  - Zero third-party dependency injection library requirement.
* **Negative:**
  - Composition Root must be kept updated when adding new ports or adapter implementations.
