# Concurrency Audit

This document reviews the thread safety, concurrency model, and execution robustness of the Salesforce AppExchange Scraper.

---

### Thread Pool Execution and Executor Choice
- **Current Implementation**: TransformationService uses a `ThreadPoolExecutor` and uses `executor.map(self.process_partner, partners)` to fetch page details concurrently.
- **Strengths**: Mapping results in order is clean. Concurrency is ideal for fetching data from network sockets where I/O blocking dominates.
- **Weaknesses**: `executor.map` raises exceptions immediately when iterating the results if any task fails. Since there is no error interception inside `process_partner`, any single HTTP exception will crash the entire pipeline.
- **Risks**: High pipeline fragility due to network dropouts or single-page errors.
- **Engineering Recommendation**: Switch to using `executor.submit` and processing tasks via `concurrent.futures.as_completed(futures)`. This allows logging individual page failures, skipping them, and continuing to collect all other successful runs.
- **Priority**: High
- **Impact**: High
- **Estimated Effort**: S

---

### Thread Safety and State Mutation
- **Current Implementation**: Each thread runs `process_partner(partner)` which modifies the input `partner` dictionary in-place by adding `html_status` or merging scraped details.
- **Strengths**: Avoids creating new memory copies of base dictionaries.
- **Weaknesses**: Modifying shared mutable collections across concurrent threads is a common concurrency code smell. While python dictionaries are relatively thread-safe for basic key additions under CPython due to the GIL, in-place mutations complicate tracking and can introduce subtle race conditions if nested attributes are mutated.
- **Risks**: Data corruption or race conditions if any background operations attempt to read the list of partners before the transformation pool completes.
- **Engineering Recommendation**: Enforce immutability. Each worker thread should copy its input partner dictionary, perform transformations, and return a new dictionary instance.
- **Priority**: Medium
- **Impact**: Medium
- **Estimated Effort**: S

---

### Worker Sizing and CPU Thrashing
- **Current Implementation**: The pool sizes default to `MAX_WORKERS = 8`.
- **Strengths**: Reasonable default limit for modest API scraping tasks.
- **Weaknesses**: Hardcoded value. 8 workers might be too small for scraping thousands of pages (very slow) and too high for systems with single-core constraints.
- **Risks**: Network congestion or server rate-limits if worker counts are scaled too high, or slow runs if set too low.
- **Engineering Recommendation**: Dynamically determine worker sizes based on configuration environment parameters or base CPU core counts combined with network latency multipliers. Allow configuring `MAX_WORKERS` in `.env`.
- **Priority**: Medium
- **Impact**: Medium
- **Estimated Effort**: XS
