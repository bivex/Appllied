# ADR-0003: Implement Dual-Path Execution Strategy (FAST vs ACCURATE)

* **Status:** Accepted
* **Deciders:** Product Engineering, Performance Optimization Working Group
* **Date:** 2026-08-05
* **ISO 42010 Clause Alignment:** §6.1 Functional Viewpoint & §8.2 Quality Attributes

## Context and Problem Statement

Different OCR use cases present opposing non-functional requirements:
1. **Interactive / Real-time scanning:** Scanning live video frames or preview viewports requires sub-30ms latency with minimal battery consumption.
2. **Document Archival / Complex Extraction:** Ingestion of multi-page PDFs, complex forms, receipts, or handwriting requires maximal recognition accuracy, language model beam search, and structural layout recovery.

A single fixed configuration cannot satisfy both low-latency and maximum-accuracy requirements efficiently.

## Decision Drivers

* SLA Latency Target: < 30ms per frame for interactive scanning.
* SLA Accuracy Target: > 98% character accuracy for complex document ingestion.
* Resource Efficiency: Minimizing CPU/GPU thermal impact during continuous scanning.

## Considered Options

1. **Option 1: Fixed Accurate Engine Configuration** (Single path).
2. **Option 2: Configurable Dual-Path Strategy Pattern (`PathSelectionStrategy`)**.
3. **Option 3: Adaptive Dynamic Throttle** based on system load.

## Decision Outcome

**Chosen Option:** **Option 2 (Configurable Dual-Path Strategy Pattern)**.

### Execution Path Specifications:
- **`RecognitionMode.FAST`**:
  - Sets Vision request `recognitionLevel` to `VNRequestTextRecognitionLevelFast`.
  - Disables language model correction (`usesLanguageCorrection = False`).
  - Optimized for real-time bounding box detection, barcode/text region tracking, and interactive viewports (~10-25ms execution).
- **`RecognitionMode.ACCURATE`**:
  - Sets Vision request `recognitionLevel` to `VNRequestTextRecognitionLevelAccurate`.
  - Enables deep neural network language modeling (`usesLanguageCorrection = True`).
  - Configures custom language priors, dictionary hints, and full structural hierarchy extraction (`Paragraph`, `Table`, `Entity` recognition).

### Consequences

* **Positive:**
  - High flexibility: Clients can explicitly request `FAST` or `ACCURATE` modes or let `PathSelectionStrategy` auto-select based on SLA constraints.
  - Optimal resource consumption for mobile and desktop runtimes.
* **Negative:**
  - Double path maintaining requirement in `VisionOCRAdapter` and domain DTO mappers.
