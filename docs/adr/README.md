# Architectural Decision Records (ADRs)

This directory contains the Architectural Decision Records (ADRs) for the **Appllied OCR System**, compliant with **ISO/IEC/IEEE 42010:2011 Clause 7**.

## 📑 ADR Index

| ADR ID | Title | Status | Date | Decision Drivers |
|---|---|---|---|---|
| [`ADR-0000`](0000-use-madr-format.md) | Record Architecture Decisions Using MADR Format | **Accepted** | 2026-08-05 | Standardization, Traceability, ISO 42010 Governance |
| [`ADR-0001`](0001-hexagonal-architecture-ports-and-adapters.md) | Adopt Hexagonal (Ports & Adapters) Architecture | **Accepted** | 2026-08-05 | Decoupling Domain Core, Framework Independence, Testability |
| [`ADR-0002`](0002-apple-vision-framework-via-pyobjc.md) | Use Apple Vision Framework via PyObjC as Primary Engine | **Accepted** | 2026-08-05 | On-Device Neural Processing, Hardware Acceleration, Privacy |
| [`ADR-0003`](0003-two-path-recognition-strategy.md) | Implement Dual-Path Execution Strategy (FAST vs ACCURATE) | **Accepted** | 2026-08-05 | Trade-off between Real-time Latency and Complex Structural Accuracy |
| [`ADR-0004`](0004-pure-python-domain-layer-zero-dependencies.md) | Pure Python Zero-Dependency Domain Layer | **Accepted** | 2026-08-05 | Domain Isolation, Security, Long-term Maintainability |
| [`ADR-0005`](0005-dependency-injection-composition-root.md) | Centralized Composition Root and Dependency Injection | **Accepted** | 2026-08-05 | Configuration Flexibility, Adapter Interchangeability |
| [`ADR-0006`](0006-poppler-pdf2image-rendering-pipeline.md) | Poppler & PDF2Image Pipeline for Document PDF OCR | **Accepted** | 2026-08-05 | High-resolution PDF Rasterization, Multi-page Concurrency |

---

## 🏛️ Standard Template Structure (MADR 3.0)

Each ADR in this directory adheres to the following structure:
- **Context & Problem Statement**: The architectural challenge or motivation.
- **Decision Drivers**: Key criteria influencing the decision (quality attributes, constraints).
- **Considered Options**: Explored alternatives and technical paths.
- **Decision Outcome**: Chosen option and key rationale.
- **Pros & Cons / Trade-offs**: Consequences, mitigation strategies, and impact on NFRs.
