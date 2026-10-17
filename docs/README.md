# Documentation Hub

Welcome to the documentation for the Salesforce AppExchange Partner Scraper & Data Pipeline. The documentation is organized into focused subdirectories:

## Directory Structure

```text
docs/
├── api/
│   └── api-specification-and-history.md   # Reverse-engineered API specs & 1,998 vs 2,150 count breakdown
├── architecture/
│   ├── architecture.md                    # Core architecture & design trade-offs
│   ├── concurrency.md                     # Threading model and session pooling
│   ├── configuration.md                   # Environment variables and filter configs
│   ├── data_dictionary.md                 # 31-column schema specification and types
│   ├── engineering-decisions.md           # Architecture Decision Records (ADRs)
│   ├── logging-strategy.md                # Structured logging conventions
│   ├── performance.md                     # Bottlenecks and optimization strategies
│   └── pipeline-flow.md                   # Visual sequence and ETL execution flow
├── planning/
│   ├── future-roadmap.md                  # High-level vision and roadmap items
│   └── plan-modern-v3-scraper.md          # Phased plan to integrate the modern v3 scraper engine
└── reviews/
    ├── code-review.md                     # Code quality audit and gap analysis
    └── repository-review.md               # Repository health and production readiness review
```

---

## Subdirectory Details

### 1. [API Specifications & History](api/api-specification-and-history.md)
Detailed analysis of the two underlying Salesforce AppExchange architectures:
- **Legacy Visualforce Remoting (`findpartners.salesforce.com`)**: Primary country queries yielding 1,998 US consultants.
- **Modern REST Recommendations API (`api.appexchange.salesforce.com/recommendations/v3/listings`)**: Marketplace discovery API returning 2,150 US consultants with cursor pagination (`searchQueryId`).

### 2. Architecture & Design
- [System Architecture](architecture/architecture.md): High-level system design and component interactions.
- [Data Dictionary](architecture/data_dictionary.md): Comprehensive 31-column output dictionary.
- [Engineering Decisions (ADRs)](architecture/engineering-decisions.md): Architecture Decision Records for key technical trade-offs.
- [Pipeline Flow](architecture/pipeline-flow.md): Step-by-step extraction, transformation, enrichment, and export stages.
- [Concurrency](architecture/concurrency.md): ThreadPoolExecutor and thread-local session management.
- [Configuration](architecture/configuration.md): Runtime parameters, filters, and flags.
- [Performance](architecture/performance.md): Performance benchmarks and memory considerations.
- [Logging Strategy](architecture/logging-strategy.md): Standardized logger levels and formatting.

### 3. Implementation Plans
- [Modern Engine Implementation Plan](planning/plan-modern-v3-scraper.md): Step-by-step phased execution plan to integrate the modern v3 AppExchange scraper engine.
- [Future Roadmap](planning/future-roadmap.md): Planned capabilities, streaming exporters, and multi-cloud extensions.

### 4. Audits & Reviews
- [Code Review](reviews/code-review.md): Audit findings, bug classifications, and resolutions.
- [Repository Review](reviews/repository-review.md): Repository health check and packaging standards.

