# Logging Strategy Audit

This document reviews the logging strategy and observabilities of the Salesforce AppExchange Scraper.

---

### Logger Configuration and Root Setup
- **Current Implementation**: `src/utils/logger.py` configures logging via `logging.basicConfig(level=logging.INFO)` at the module level.
- **Strengths**: Immediate global availability of formatting and log limits.
- **Weaknesses**: Modifying basicConfig on module import forces this config onto any other libraries imported into the script. This causes side effects in testing and multi-module pipelines.
- **Risks**: Messy test output logs and library log interference.
- **Engineering Recommendation**: Wrap logging configuration in a setup function (e.g. `setup_logging()`) and invoke it inside the `main()` block of `src/main.py`.
- **Priority**: Low
- **Impact**: Medium
- **Estimated Effort**: XS

---

### Log Verbosity and Redundancy
- **Current Implementation**: `HtmlTransformation` prints debug messages on every component parsed (e.g., `logger.debug("Parsing metadata...")`, `logger.debug("Parsing statistics...")`).
- **Strengths**: Highly detailed trace information for local debugging.
- **Weaknesses**: When scraping thousands of pages concurrently with multiple workers, these log entries will generate massive amounts of log files, cluttering standard output and disk space.
- **Risks**: Log storage exhaustion and performance degradation due to print/file writes.
- **Engineering Recommendation**: Remove fine-grained method-level debug statements or downgrade them to a custom TRACE level. Only log progress on partner completion or overall stages.
- **Priority**: Medium
- **Impact**: Medium
- **Estimated Effort**: S

---

### Exception Logging and Context
- **Current Implementation**: Most services use `logger.exception()` to log failures and re-raise.
- **Strengths**: Captures full traceback details, helping to trace unexpected bugs.
- **Weaknesses**: Re-raising an exception after logging it at every nested layer results in duplicate traceback logs. For example, if `HtmlClient` logs and re-raises, and `TransformationService` logs and re-raises, the same failure is printed multiple times.
- **Risks**: Bloated log files with duplicated stacks.
- **Engineering Recommendation**: Only log full exceptions at boundary layers (like the top-level `Pipeline.run`). Inner layers should raise custom typed exceptions with clear messages, logging only warnings or contextual details.
- **Priority**: Medium
- **Impact**: Medium
- **Estimated Effort**: S

---

### Production Logging Strategy
- **Current Implementation**: Logs to standard output and redirects to a flat file `scraper.log` (as listed in gitignore).
- **Strengths**: Simple file output.
- **Weaknesses**: Flat text logs are difficult to parse in cloud monitoring environments (e.g., AWS CloudWatch, Datadog, ELK stack).
- **Risks**: Lack of structural searchability in production logs.
- **Engineering Recommendation**: Integrate a structured JSON logger (e.g., using `python-json-logger`) for production runs. This outputs structured JSON lines containing fields like `timestamp`, `level`, `module`, `partner_id`, and `message`, making it easy to query and monitor.
- **Priority**: Medium
- **Impact**: High
- **Estimated Effort**: S
