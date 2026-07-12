# Future Roadmap

This document outlines structural recommendations for scaling, incremental loading, and orchestrator integrations.

---

### Airflow and Workflow Orchestrator Compatibility
- **Current Implementation**: The pipeline runs as a single, sequential Python script via `src/main.py`.
- **Strengths**: Simple execution via CLI. No orchestrator dependencies.
- **Weaknesses**: Cannot be scheduled, monitored, or retried at the task level by workflow orchestrators like Apache Airflow, Prefect, or Dagster.
- **Risks**: Failure in one stage requires re-running the entire script, violating task atomicity.
- **Engineering Recommendation**: Decouple the pipeline stages into independent CLI commands (e.g., `python -m src.cli extract`, `python -m src.cli transform`, `python -m src.cli export`). This allows an Airflow DAG to invoke each step as separate tasks (e.g., using `BashOperator` or `PythonOperator`), passing data using intermediate cloud storage (S3/GCS).
- **Priority**: Medium
- **Impact**: High
- **Estimated Effort**: M

---

### Incremental vs. Batch Processing
- **Current Implementation**: The pipeline runs in full-batch mode, extracting and scraping all partners in every run.
- **Strengths**: Guarantees data freshness and completeness.
- **Weaknesses**: Heavy network load, long running times, and high API usage for static records that rarely change.
- **Risks**: High risk of getting IP-blocked or rate-limited by Salesforce due to scraping unchanged pages repeatedly.
- **Engineering Recommendation**: Implement incremental loading. Save a hash of the previous scrape output. In the extraction phase, compare record timestamps or hash signatures. If a partner record was updated, queue it for scraping; otherwise, reuse the cached data from the previous run.
- **Priority**: High
- **Impact**: Critical
- **Estimated Effort**: L

---

### Database Export Abstraction
- **Current Implementation**: Outputs are written to JSON and CSV files via `ExportService`.
- **Strengths**: Simple file outputs, easy to load manually.
- **Weaknesses**: Lacks support for writing to production databases (PostgreSQL, Snowflake, BigQuery) which are standard in corporate data pipelines.
- **Risks**: Downstream systems must parse CSV files from disk, which is fragile and hard to synchronize.
- **Engineering Recommendation**: Introduce an abstract `BaseExporter` interface. Implement `FileExporter` and `DatabaseExporter` (using SQLAlchemy or target data warehouse SDKs) to load data directly into target staging tables with support for upsert (UPSERT/MERGE) operations.
- **Priority**: Medium
- **Impact**: High
- **Estimated Effort**: M
