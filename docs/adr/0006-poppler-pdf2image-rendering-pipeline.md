# ADR-0006: Poppler & PDF2Image Pipeline for Document PDF OCR

* **Status:** Accepted
* **Deciders:** Document Processing Team, Performance Lead
* **Date:** 2026-08-05
* **ISO 42010 Clause Alignment:** §6.1 Functional & Deployment Viewpoints & §8.2 Quality Attributes

## Context and Problem Statement

Document ingestion pipelines frequently process multi-page PDF files containing vector text, scanned images, or mixed layouts. Apple Vision framework operates natively on image buffers (`CGImageRef`, `NSImage`, or PIL images) rather than raw multi-page PDF binaries.

How should multi-page PDF files be converted into high-fidelity image streams for engine consumption while maintaining high throughput and memory stability?

## Decision Drivers

* High Rendering Resolution: Render PDF pages at configurable DPI (200-300 DPI) to optimize OCR character extraction accuracy.
* Multi-page Concurrency: Support batch rendering and page parallelization for large PDF documents.
* Graceful Fallback: Detect missing Poppler system binaries and provide actionable error messaging or native fallback image extractors.

## Considered Options

1. **Option 1: Poppler CLI backend via `pdf2image` library** with configurable DPI and thread pool worker rendering.
2. **Option 2: Pure Python PDF renderers** (e.g., `pypdf`, `pdfplumber`).
3. **Option 3: macOS Quartz `PDFDocument` API via PyObjC**.

## Decision Outcome

**Chosen Option:** **Option 1 (Poppler & `pdf2image` rendering pipeline)** as primary rasterizer with macOS Quartz API integration.

### Implementation Architecture:
- PDF files are loaded via `LocalFileImageSource` or `PDFDocumentSource`.
- Pages are rasterized at 300 DPI into uncompressed memory buffers (`RGB`).
- Multi-page processing executes with worker pools (`ProcessPoolExecutor`) to maximize throughput across CPU cores.

### Consequences

* **Positive:**
  - Exceptional rasterization quality and sub-pixel clarity for thin fonts and historical documents.
  - Scalable multi-page document throughput (processes 20+ pages/sec under concurrent worker pools).
* **Negative:**
  - System requirement for `poppler` binary installation (`brew install poppler` on macOS).
