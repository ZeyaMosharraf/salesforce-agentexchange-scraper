# Configuration Management Audit

This document reviews the configuration architecture of the Salesforce AppExchange Scraper.

---

### dataclass Settings Configuration
- **Current Implementation**: The project uses a custom frozen dataclass `Settings` loading settings via `os.getenv` in `src/config/settings.py`.
- **Strengths**: Simple implementation with zero dependencies beyond `dotenv`. Immutable configuration properties.
- **Weaknesses**: No type checking or coercion at startup. For instance, if an environment variable is loaded as a string, it must be manually cast (e.g. `int(os.getenv("REQUEST_TIMEOUT", "30"))`), which can throw unhandled exceptions if the environment file is misconfigured.
- **Risks**: Application crash at runtime due to malformed string conversions in settings initialization.
- **Engineering Recommendation**: Migrate configuration management to Pydantic Settings (`pydantic-settings`). Pydantic provides type coercion, default values, validation errors at startup, and environment name mapping.
- **Priority**: High
- **Impact**: High
- **Estimated Effort**: S

---

### Hardcoded Configuration and Constants
- **Current Implementation**: Several configuration values are hardcoded in modules rather than defined in `settings.py`. Examples include `MAX_WORKERS = 8` in `settings.py` (not fetched from env), and search payload classnames like `@udd/01p3m00000EBlzK` in `partner_filter.py`.
- **Strengths**: Keeps settings instantiation straightforward.
- **Weaknesses**: Changing concurrency levels or targeting a different Salesforce controller requires code modifications.
- **Risks**: Inability to adjust concurrency dynamically when running in environment constraints (e.g., lower worker count in CI/CD).
- **Engineering Recommendation**: Move `MAX_WORKERS`, target API classnames, and output file paths to the `Settings` class, loading them from environment variables with sensible defaults.
- **Priority**: High
- **Impact**: High
- **Estimated Effort**: S

---

### Environment File and Secret Loading
- **Current Implementation**: Loads `.env` file from the project base directory on module import.
- **Strengths**: Automatic setup of local environment properties.
- **Weaknesses**: Loading dotenv globally on import can cause issues in testing where mock environments are required.
- **Risks**: Environment bleed between test runs and active runs.
- **Engineering Recommendation**: Load environment files inside a configuration initializer rather than at the top level of the config package module.
- **Priority**: Low
- **Impact**: Medium
- **Estimated Effort**: XS
