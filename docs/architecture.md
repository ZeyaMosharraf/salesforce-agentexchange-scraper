# Architectural Audit

This document presents a complete architectural review of the Salesforce AppExchange Scraper pipeline.

---

### Architectural Design and Cohesion
- **Current Implementation**: The system implements a modular ETL (Extract-Transform-Load) design. Extraction (`ExtractionService`) collects JSON chunks from the search API. Transformation (`TransformationService`) coordinates concurrent page retrieval and text mining. Export (`ExportService`) dumps files. Orchestration (`Pipeline`) handles control flow.
- **Strengths**: High cohesion within individual service files. Clear boundaries between HTTP handling (`clients`), business logic (`services`), and serialization/data mapping (`transformations`).
- **Weaknesses**: The orchestration layer is too tightly coupled to specific export file paths and service instances, rather than accepting them as configurable dependencies.
- **Risks**: Modifying output file names or adding new sources requires code changes in `pipeline.py` rather than configuration adjustments.
- **Engineering Recommendation**: Use Dependency Injection to pass configured clients and settings to services instead of hardcoding service instantiation within `Pipeline.__init__`.
- **Priority**: Medium
- **Impact**: High
- **Estimated Effort**: S

---

### Coupling and Dependency Injection
- **Current Implementation**: Services instantiate their dependencies internally (e.g., `ExtractionService` instantiates `SalesforceClient` in its constructor, `TransformationService` instantiates `HtmlClient` and transformations).
- **Strengths**: Simple instantiation. No setup boilerplate in the entrypoint.
- **Weaknesses**: Hard to mock dependencies for unit testing. High coupling between services and clients.
- **Risks**: Writing unit tests requires monkeypatching or network mocking libraries (like `responses` or `requests-mock`) rather than passing mock class instances.
- **Engineering Recommendation**: Refactor constructors to accept clients as optional parameters, defaulting to standard clients if none are provided.
- **Priority**: High
- **Impact**: High
- **Estimated Effort**: S

---

### Data Pipeline Flow and Orchestration
- **Current Implementation**: The orchestrator (`src/orchestrator/pipeline.py`) executes the three phases sequentially. It has a single `run` method that handles raw outputs, processed objects, and exports.
- **Strengths**: Linear and easy-to-follow execution path. Ideal for single-run cron tasks.
- **Weaknesses**: No execution state tracking. If the transformation or export phase fails, the extracted raw API data is lost, requiring a full re-query of the Salesforce API on the next run.
- **Risks**: Network failures on page scraping after an hour of API extraction will discard all progress, leading to unnecessary API load and rate limits.
- **Engineering Recommendation**: Implement a checkpointing or staging mechanism where raw API outputs are saved to disk (e.g., `output/raw/`) before transformation, allowing the pipeline to resume from the last successful stage.
- **Priority**: High
- **Impact**: High
- **Estimated Effort**: M

---

### Missing Abstractions and Extensibility
- **Current Implementation**: Scraper is built specifically for Salesforce AppExchange. There are no base classes or interfaces for clients, transformation layers, or export formats.
- **Strengths**: Minimal abstraction overhead, keeping the code simple and avoiding premature generalization.
- **Weaknesses**: Difficult to extend the scraper to support other platforms or write to databases (like PostgreSQL) without rewriting or duplicating the export logic.
- **Risks**: Adding a database export requires editing `ExportService` directly, violating the Open-Closed Principle.
- **Engineering Recommendation**: Define abstract interfaces or protocols (using Python's `typing.Protocol` or `abc.ABC`) for `BaseClient`, `BaseTransformation`, and `BaseExporter`.
- **Priority**: Low
- **Impact**: Medium
- **Estimated Effort**: M
