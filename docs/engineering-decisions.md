# Engineering Decisions Audit

This document reviews the major design and engineering trade-offs in the Salesforce AppExchange Scraper.

---

### Reverse-Engineered Apex API vs. Official API
- **Current Implementation**: The pipeline sends POST requests directly to Salesforce's internal search handler endpoint (`findpartners.salesforce.com/webruntime/api/apex/execute`) using a reverse-engineered query payload.
- **Strengths**: Bypasses authentication and OAuth flow requirements, allowing public guest-access scraping. Accesses complete, structured lists of partners directly.
- **Weaknesses**: The API payload contains fragile, undocumented parameters like `classname: "@udd/01p3m00000EBlzK"`. If Salesforce refactors their internal Apex controller, the scraper will immediately fail.
- **Risks**: High risk of sudden pipeline breakage without notice from Salesforce.
- **Engineering Recommendation**: Maintain a test suite that runs a sanity check on this endpoint. Keep the classname and endpoint path configurable in `settings.py` so they can be updated quickly without refactoring code.
- **Priority**: High
- **Impact**: High
- **Estimated Effort**: S

---

### Concurrent ThreadPoolExecutor vs. Asyncio
- **Current Implementation**: Concurrency is managed via `ThreadPoolExecutor` mapping over partner listing URLs.
- **Strengths**: Highly suited for I/O-bound operations in Python where the `requests` library is used (which is synchronous and blocking). Simple implementation without async/await boilerplates.
- **Weaknesses**: Threads consume more memory and system resources than async event loops. Cannot scale efficiently beyond a few dozen concurrent requests.
- **Risks**: Setting a high thread count could cause thread thrashing and high CPU overhead on systems running the scraper.
- **Engineering Recommendation**: Keep thread pools at moderate sizes (e.g. 8-16). If the listing count scales past 10,000, consider refactoring the network clients to use `httpx` or `aiohttp` combined with `asyncio`.
- **Priority**: Medium
- **Impact**: Medium
- **Estimated Effort**: L

---

### BeautifulSoup HTML Scraping vs. Headless Browser (Playwright)
- **Current Implementation**: Listing pages are parsed as static HTML using `BeautifulSoup` and `lxml`.
- **Strengths**: Extremely fast and lightweight. Requires low memory and CPU resources compared to rendering pages in a browser.
- **Weaknesses**: Static scrapers cannot capture elements rendered dynamically via client-side JavaScript.
- **Risks**: If Salesforce shifts AppExchange listing pages to a client-side Single Page Application (SPA), the HTML scraper will fetch empty shells and fail.
- **Engineering Recommendation**: Verify if all critical listing page data is populated in the initial server-delivered HTML. If dynamic UI elements (like dynamic reviews or charts) are required, migrate to a headless browser client using Playwright.
- **Priority**: Low
- **Impact**: High
- **Estimated Effort**: L

---

### Dictionary-Based Data Flow vs. Pydantic Models
- **Current Implementation**: Data is passed as raw dictionaries (`dict[str, Any]`) throughout the pipeline.
- **Strengths**: Zero validation overhead, maximum flexibility, and fast serialization.
- **Weaknesses**: No runtime type safety or schema validation. A field typo in `partner_transformation.py` or `html_transformation.py` will propagate silently until the data export phase or database loading.
- **Risks**: Data corruption or missing fields in output CSVs without validation exceptions.
- **Engineering Recommendation**: Adopt Pydantic models for the data transfer objects (`PartnerAPIModel`, `PartnerHTMLModel`, `EnrichedPartnerModel`). This enforces schemas, type checks, and validation at boundary points.
- **Priority**: High
- **Impact**: High
- **Estimated Effort**: M
