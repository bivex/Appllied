# Changelog

All notable changes to the **Appllied / OCR System** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **ISO Audit Compliance**: Added MIT `LICENSE` file and `sbom.json` generation tool for ISO/IEC 19770.
- **Documentation Suite**: Added comprehensive `docs/ARCHITECTURE.md` with Mermaid diagrams, DDD domain model, and Hexagonal layer maps.

## [0.1.0] - 2026-08-05

### Added
- **Core Domain Engine**:
  - Domain aggregates (`Document`, `OCRAggregate`) and value objects (`BoundingBox`, `Point`, `Polygon`, `Language`).
  - Hierarchical text model (`TextLine` -> `Word` -> `Character`).
  - Structure recognition for Paragraphs, Tables, and Named Entities (email, phone, URL).
- **Hexagonal Architecture (Ports & Adapters)**:
  - `OCREngine` port with `VisionOCRAdapter` (Apple Vision Framework) and `CustomModelOCRAdapter` (CoreML / ANE).
  - `ImageSource` port supporting `LocalFileImageSource` and `HttpImageSource`.
  - `DocumentRepository` port with `InMemoryDocumentRepository`.
- **Application & Use Cases**:
  - `ProcessDocumentUseCase`, `ExtractStructureUseCase`, `GetDocumentUseCase`, and `SearchDocumentsUseCase`.
  - Path selection strategy supporting `FAST` vs `ACCURATE` OCR execution.
  - Language correction domain service (`LanguageCorrectionService`).
- **CLI Utilities & Scripts**:
  - `ocr-extract`: CLI tool for text extraction from image files.
  - `ocr-extract-pdf`: CLI tool for multi-page PDF processing via Quartz/PDFKit rendering.
  - `ocr-generate`: Synthetic test data generation utility.
  - `ocr-sbom`: Software Bill of Materials inventory generator.
- **Dependency Injection**: Container composition root (`container.py`).
