# Non-Functional Requirements (NFR) & Quality Attribute Specification

> **Appllied — System Quality Attributes & NFR Specification**  
> **Standard Alignment:** ISO/IEC 25010:2011 System & Software Quality Model and ISO/IEC/IEEE 42010:2011 §8.2

---

## 1. Quality Attribute Utility Tree

| Quality Attribute | Ref ID | Attribute Refinement | SLA Target / Measurable Metric | Verification Method |
|---|---|---|---|---|
| **Performance Efficiency** | `NFR-PERF-01` | FAST Path Processing Latency | $\le 30\text{ ms}$ per single page frame | Automated Benchmark Suite |
| **Performance Efficiency** | `NFR-PERF-02` | ACCURATE Path Latency | $\le 150\text{ ms}$ per standard letter document | Performance Profiler |
| **Performance Efficiency** | `NFR-PERF-03` | PDF Rendering Throughput | $\ge 20\text{ pages/sec}$ at 300 DPI (8-core M-series CPU) | Load Test Runner |
| **Reliability** | `NFR-REL-01` | Fallback Engine Availability | 100% graceful fallback to `CustomModelOCRAdapter` if PyObjC unavailable | Unit / Integration Test |
| **Reliability** | `NFR-REL-02` | Invalid Input Handling | 0 unhandled fatal crashes on corrupt/malformed PDF/image inputs | Fuzzing & Negative Testing |
| **Security & Privacy** | `NFR-SEC-01` | On-Device Isolation | 0 external network requests during OCR execution pipeline | Static Code & Socket Audit |
| **Security & Privacy** | `NFR-SEC-02` | Memory Hygiene | In-memory image buffers purged immediately after text line extraction | Memory Leak Profiler |
| **Maintainability** | `NFR-MAINT-01` | Domain Layer Independence | 0 external third-party package dependencies in `ocr_system/domain/` | Automated AST Linter |
| **Maintainability** | `NFR-MAINT-02` | Unit Test Execution Speed | 100% core domain test suite execution in $< 0.1\text{ s}$ | Pytest Test Runner |
| **Portability** | `NFR-PORT-01` | Cross-Platform Compatibility | Core domain & CLI usable across macOS, Linux, and Windows runtimes | Multi-OS CI Workflow |

---

## 2. Detailed NFR Specifications

### 2.1 Performance Efficiency (ISO 25010 §4.2)

- **`NFR-PERF-01` (FAST Mode Latency):**
  - **Requirement:** When `RecognitionMode.FAST` is requested, the system must complete OCR detection, line extraction, and domain mapping in $\le 30\text{ ms}$ per image frame on Apple Silicon hardware.
  - **Rationale:** Interactive scanning viewports and real-time document preview feeds require 30+ FPS refresh capability.

- **`NFR-PERF-02` (ACCURATE Mode Latency):**
  - **Requirement:** When `RecognitionMode.ACCURATE` is requested with language correction and paragraph structure recovery, processing time per standard document page (A4 / Letter) must not exceed $150\text{ ms}$.

- **`NFR-PERF-03` (Memory Footprint & Peak Budget):**
  - **Requirement:** Total system RAM consumption during batch ingestion of a 100-page PDF file must remain $< 512\text{ MB}$.
  - **Enforcement:** Page images are loaded and processed iteratively using generator streams rather than buffering the entire rasterized document in RAM simultaneously.

---

### 2.2 Reliability & Fault Tolerance (ISO 25010 §4.3)

- **`NFR-REL-01` (Engine Degradation & Fallbacks):**
  - **Requirement:** If PyObjC or macOS Vision Framework bindings fail to initialize (e.g., executing inside a Linux container or headless server), `OCRContainer` must transparently fall back to `CustomModelOCRAdapter` without throwing unhandled `ImportError` or `AttributeError` exceptions.

- **`NFR-REL-02` (Input Validation & Error Boundaries):**
  - **Requirement:** Image sources (`LocalFileImageSource`, `HttpImageSource`) must validate image headers, dimensions, and color profiles prior to engine invocation. Invalid files must raise explicit domain exceptions (`InvalidImageSourceError`, `DocumentProcessingError`).

---

### 2.3 Security & Data Confidentiality (ISO 25010 §4.4)

- **`NFR-SEC-01` (100% On-Device Air-Gapped Privacy):**
  - **Requirement:** All OCR processing, text recognition, feature extraction, and structure parsing must execute strictly on local CPU/GPU/ANE hardware. No image bytes, recognized text, or metadata may leave the local process boundary.

- **`NFR-SEC-02` (Input Sanitization & Buffer Security):**
  - **Requirement:** File paths passed to CLI and API entry points must be sanitized against path traversal vulnerabilities (e.g. `../` escapes). Image data loaded into RAM must be unreferenced and collected by Python GC immediately following processing.

---

### 2.4 Maintainability & Modularity (ISO 25010 §4.5)

- **`NFR-MAINT-01` (Clean Domain Encapsulation):**
  - **Requirement:** The domain layer (`ocr_system/domain/`) must contain zero imports from third-party modules. Only standard library modules (`dataclasses`, `enum`, `typing`, `uuid`, `datetime`) are permitted.

- **`NFR-MAINT-02` (Automated Test Suite Performance):**
  - **Requirement:** Fast unit test execution must be maintained. The domain test suite must execute in $< 100\text{ ms}$ on standard developer workstations to support continuous local test execution during development.

---

### 2.5 Portability & System Compatibility (ISO 25010 §4.7)

- **`NFR-PORT-01` (Platform Adaptability):**
  - **Requirement:** The application layer, domain models, and CLI scripts must be 100% platform-agnostic, running seamlessly on macOS (Darwin), Linux, and Windows. Native hardware acceleration (Apple Vision / PyObjC) is conditionally activated when running on macOS.
