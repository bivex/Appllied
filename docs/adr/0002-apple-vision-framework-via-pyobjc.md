# ADR-0002: Use Apple Vision Framework via PyObjC as Primary Engine

* **Status:** Accepted
* **Deciders:** OCR Engine Team, Security Auditor
* **Date:** 2026-08-05
* **ISO 42010 Clause Alignment:** §6.1 Deployment Viewpoint & §7 Architectural Rationale

## Context and Problem Statement

To deliver high-throughput, low-latency OCR with multi-language and pencil/handwriting support on macOS devices, Appllied requires a native OCR backend. Cloud-based OCR services incur latency and privacy risks, while pure Python software engines (e.g., Tesseract wrappers) underutilize Apple Silicon Neural Engine (ANE) hardware.

## Decision Drivers

* **Performance & Acceleration:** Utilize Apple Neural Engine (ANE) and Metal GPU hardware acceleration on Apple Silicon (M1/M2/M3/M4).
* **Privacy & Security:** Complete on-device processing without sending sensitive documents over the network.
* **Accuracy:** High accuracy for standard printed text, receipts, forms, and handwritten notes via Apple Vision framework (`VNRecognizeTextRequest`).

## Considered Options

1. **Option 1: Apple Vision Framework via PyObjC (`Vision.framework` & `Quartz.framework`)**.
2. **Option 2: Cloud API Integration** (AWS Textract, Google Cloud Vision, Azure Form Recognizer).
3. **Option 3: Tesseract OCR (`pytesseract`)**.

## Decision Outcome

**Chosen Option:** **Option 1 (Apple Vision Framework via PyObjC)** as the primary production engine adapter (`VisionOCRAdapter`).

### Implementation Rationale:
- `VNRecognizeTextRequest` executes directly on ANE/GPU hardware.
- Native integration provides word and character bounding box coordinates normalized to `[0, 1]` viewport boundaries.
- Graceful fallback mechanism implemented in `CustomModelOCRAdapter` when PyObjC or macOS Vision APIs are unavailable on non-macOS environments.

### Consequences

* **Positive:**
  - Zero external network dependencies (100% on-device data privacy).
  - High processing throughput (~30-80ms per document page on Apple Silicon).
  - Native support for multilingual text recognition and custom language dictionaries.
* **Negative:**
  - Platform dependency on macOS for native execution; cross-platform execution relies on fallback adapter.
