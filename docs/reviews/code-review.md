# Module-by-Module Code Review

This document provides a detailed, file-by-file code review of all active modules in the repository.

---

### `src/main.py`
- **Responsibility**: Application entry point. Instantiates and executes the pipeline orchestration.
- **Code Smell**: None. It is clean and minimal.
- **Complexity**: Extremely Low.
- **Readability / Maintainability**: Excellent.
- **Engineering Recommendation**: None.
- **Priority**: Low | **Impact**: Low | **Estimated Effort**: XS

---

### `src/orchestrator/pipeline.py`
- **Responsibility**: Orchestrates the ETL pipeline, driving the extraction, transformation, and export services.
- **Code Smell**: Catches global `Exception` in the runner, logs it, and re-raises. This is acceptable for top-level logging, but it doesn't close or clean up resources (e.g. flushing output logs or deleting temporary files).
- **Long Methods**: `run()` is 37 lines. Not overly long, but does multiple things (coordinates three services, logs, writes multiple files).
- **Hardcoded values**: Output file paths (`output/partners.json`, `output/partners.csv`) are hardcoded in the method arguments rather than loaded from configuration.
- **Complexity**: Low.
- **Readability / Maintainability**: Moderate. It couples the sequential execution path rigidly.
- **Engineering Recommendation**: Move output file paths to `settings.py`. Use dependency injection to pass services.
- **Priority**: High | **Impact**: High | **Estimated Effort**: S

---

### `src/clients/salesforce_client.py`
- **Responsibility**: Sends HTTP POST queries to the Salesforce AppExchange internal search API.
- **Code Smell**: Hardcoded retry count (3) and backoff factor (2). The use of `allowed_methods=["POST"]` for retries is technically a violation of HTTP retry guidelines (since POST is non-idempotent), but safe here since the endpoint acts as a search query. This exception should be explicitly documented.
- **Complexity**: Low.
- **Readability / Maintainability**: Good. Well-segregated session construction.
- **Engineering Recommendation**: Make retry configuration configurable via `settings.py`. Document why retrying POST is safe.
- **Priority**: Medium | **Impact**: Medium | **Estimated Effort**: XS

---

### `src/clients/html_client.py`
- **Responsibility**: Downloads partner listing HTML pages using HTTP GET.
- **Code Smell**: Returning `None` silently on `404 Not Found` is reasonable, but raising errors for other status codes (like 500 or 403) will crash the worker thread, causing `executor.map` to raise an exception and fail the entire scraper.
- **Complexity**: Low.
- **Readability / Maintainability**: Moderate.
- **Engineering Recommendation**: Handle non-404 HTTP errors gracefully by returning a placeholder or custom exception instead of letting it raise and crash the thread runner.
- **Priority**: High | **Impact**: High | **Estimated Effort**: S

---

### `src/config/settings.py`
- **Responsibility**: Defines application settings, loading values from environment variables via `dotenv`.
- **Code Smell**: Uses a custom `@dataclass` rather than Pydantic settings. Manual type casting (like `int(os.getenv(...))`) can raise uncaught `ValueError`s if the `.env` value is non-numeric.
- **Hardcoded values**: `MAX_WORKERS = 8` is hardcoded as a class attribute rather than loaded from env.
- **Complexity**: Low.
- **Readability / Maintainability**: High.
- **Engineering Recommendation**: Refactor class to inherit from `pydantic_settings.BaseSettings` for validation and type safety.
- **Priority**: High | **Impact**: High | **Estimated Effort**: S

---

### `src/models/partner_filter.py`
- **Responsibility**: Models AppExchange query filters and formats them into a Salesforce-compatible payload.
- **Code Smell**: Default search criteria (countries, practice size) are hardcoded in the model constructor. The Salesforce Apex class identifier `classname: "@udd/01p3m00000EBlzK"` is hardcoded.
- **Complexity**: Low.
- **Readability / Maintainability**: Good, though the API payload format is rigid.
- **Engineering Recommendation**: Extract the hardcoded Salesforce Apex class string to `settings.py`. Move default filters to configuration or inject them during pipeline execution.
- **Priority**: High | **Impact**: High | **Estimated Effort**: S

---

### `src/services/extraction_service.py`
- **Responsibility**: Coordinates extraction of paginated API data.
- **Code Smell**: Critical logic bug: `offset` increments by 1 in a `while True` loop (`offset += 1`), while the payload requests a batch limit of 300 (`limit_size = 300`). If Salesforce uses row-based offset pagination (standard), this will fetch records 0-299, then 1-300, then 2-301, resulting in huge duplicates, slow queries, and risk of rate limit bans.
- **Complexity**: Moderate.
- **Readability / Maintainability**: Moderate.
- **Engineering Recommendation**: Confirm if offset is row-based. If yes, increment `offset` by `limit_size` (300) in each loop.
- **Priority**: Critical | **Impact**: Critical | **Estimated Effort**: XS

---

### `src/services/transformation_service.py`
- **Responsibility**: Coordinates the mapping of API objects and concurrent scraping of HTML pages using `ThreadPoolExecutor`.
- **Code Smell**: Exception handling wraps the entire ThreadPool execution, but does not capture errors thrown within individual thread mappings. If a single page download throws an exception, the entire transformation step crashes. Mutates the input `partner` dictionary in-place across threads.
- **Complexity**: Moderate.
- **Readability / Maintainability**: High.
- **Engineering Recommendation**: Catch errors within `process_partner` to ensure one failed listing page does not crash the entire scrape. Return new dictionary copies instead of mutating in-place.
- **Priority**: High | **Impact**: High | **Estimated Effort**: S

---

### `src/services/export_service.py`
- **Responsibility**: Exports processed partners to JSON and CSV formats.
- **Code Smell**: Shallow flattener in `_flatten_partner` only flattens dictionaries one level deep. Nested dictionaries (like `metadata_og`) remain as unflattened Python dictionaries inside the CSV cell, which violates tidy data principles.
- **Duplicate Code**: The directory creation block is duplicated in both `export_json` and `export_csv`.
- **Complexity**: Low.
- **Readability / Maintainability**: Moderate.
- **Engineering Recommendation**: Implement a recursive dictionary flattener. Extract directory creation to a utility function.
- **Priority**: Medium | **Impact**: High | **Estimated Effort**: S

---

### `src/transformations/partner_transformation.py`
- **Responsibility**: Transforms and flattens raw partner records from the Salesforce API payload.
- **Code Smell**: Accesses nested keys using `.get()`, but does not issue warnings or handle cases where critical properties (like `Id` or `AppExchange_Listing_URL__c`) are missing.
- **Complexity**: Low.
- **Readability / Maintainability**: Good.
- **Engineering Recommendation**: Log warnings if essential mapping keys are missing from the raw API payload.
- **Priority**: Low | **Impact**: Medium | **Estimated Effort**: XS

---

### `src/transformations/html_transformation.py`
- **Responsibility**: Parses partner listing pages using `BeautifulSoup` to extract metadata, company info, reviews, contact details, etc.
- **Code Smell**: Massive class size (916 lines). High complexity. Relies on fragile CSS class names and layout-specific text searching (regex) that will break easily if Salesforce changes the AppExchange frontend.
- **Long Methods**: The file has many parsing helper methods. While they are separated logically, the overall class size is a maintenance burden.
- **Dead Code**: Several scraping selectors (like `.appx-country, .country`) look for classes that may no longer exist.
- **Complexity**: High.
- **Readability / Maintainability**: Low.
- **Engineering Recommendation**: Split this class into specialized parser modules (e.g. `MetadataParser`, `ReviewParser`, `ContactParser`) to improve readability and maintainability.
- **Priority**: Medium | **Impact**: High | **Estimated Effort**: M

---

### `src/transformations/merge_transformation.py`
- **Responsibility**: Combines the API partner record dictionary with the scraped HTML dictionary.
- **Code Smell**: Over-engineered. It is a class containing a single method that calls `.update()` on a copy of a dictionary.
- **Complexity**: Low.
- **Readability / Maintainability**: High but redundant.
- **Engineering Recommendation**: Delete the module. Perform dictionary updates inline or via a simple utility function in `TransformationService` to reduce file and class bloat.
- **Priority**: Low | **Impact**: Low | **Estimated Effort**: XS

---

### `src/utils/logger.py`
- **Responsibility**: Sets up application-wide logger configurations.
- **Code Smell**: Configures the global logger using `logging.basicConfig` upon module import, causing side effects in imported environments.
- **Complexity**: Low.
- **Readability / Maintainability**: High.
- **Engineering Recommendation**: Wrap the logging configuration in a `setup_logging` function.
- **Priority**: Low | **Impact**: Medium | **Estimated Effort**: XS
