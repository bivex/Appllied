# ADR-0004: Pure Python Zero-Dependency Domain Layer

* **Status:** Accepted
* **Deciders:** Lead Systems Architect, Security Compliance Auditor
* **Date:** 2026-08-05
* **ISO 42010 Clause Alignment:** §5.2 Architectural Concerns & §6.3 Model Kinds

## Context and Problem Statement

Domain models often suffer from dependency creep when framework libraries (such as PyTorch, OpenCV, PIL/Pillow, Pydantic, or PyObjC) leak into domain entities. This compromises long-term code stability, breaks domain encapsulation, increases supply-chain attack surfaces, and hampers deterministic unit testing.

How should domain models in `ocr_system/domain/` be modeled and governed?

## Decision Drivers

* **Zero external dependencies rule:** Domain entities must compile and execute using standard Python 3 standard library modules only.
* **Immutability & Safety:** Value objects (e.g. `BoundingBox`) must be immutable, thread-safe, and self-validating.
* **Domain Event Isolation:** State changes within the aggregate root (`Document`) must publish pure Python domain events without requiring third-party event brokers.

## Considered Options

1. **Option 1: Pydantic-based domain models** (framework-bound data classes).
2. **Option 2: Pure Python dataclasses / custom immutable objects with zero third-party imports**.
3. **Option 3: Dictionary-based untyped domain structures**.

## Decision Outcome

**Chosen Option:** **Option 2 (Pure Python dataclasses and custom immutable value objects)**.

### Architectural Rules:
- All classes in `ocr_system/domain/entities.py`, `value_objects.py`, `enums.py`, and `events.py` import strictly from Python standard library (`typing`, `dataclasses`, `enum`, `uuid`, `datetime`, `math`).
- External frameworks (PyObjC, PIL, OpenCV, NumPy) are confined strictly to the **Infrastructure Layer**.

### Consequences

* **Positive:**
  - 100% deterministic domain unit tests executing in milliseconds without setup/mock overhead.
  - Immunity to third-party breaking changes or library deprecation in core business logic.
  - Strict compliance with ISO 25010 maintainability standards.
* **Negative:**
  - Standard library implementations of validation or domain event dispatches must be explicitly authored.
