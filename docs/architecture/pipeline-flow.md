# Pipeline Flow Audit

This document reviews the data and object pipeline flow of the Salesforce AppExchange Scraper.

---

### Step 1: Extraction Phase
- **Current Implementation**: `ExtractionService` fetches paginated JSON lists. The offset increases by 1 each iteration. It loops until the search returns no partners.
- **Strengths**: Structured paginated collection. It stops when the page is empty, preventing static limit issues.
- **Weaknesses**: If Salesforce API offset is row-based (which is typical for SOQL-based APIs), incrementing `offset` by 1 while requesting a `limitSize` of 300 is a critical logic bug. It will fetch records 0-299, then 1-300, then 2-301, fetching almost duplicate datasets and causing huge performance waste.
- **Risks**: Massive duplicate data, excessive network requests, and API rate limit bans.
- **Engineering Recommendation**: Verify if the API offset is page-based or row-based. If it is row-based, increment `offset` by `limit_size` (300) in each iteration.
- **Priority**: Critical
- **Impact**: Critical
- **Estimated Effort**: XS

---

### Step 2: Transformation and Enrichment Phase
- **Current Implementation**: For each extracted partner record, the client downloads the HTML listing page, parses details via `HtmlTransformation`, and calls `MergeTransformation` to merge the dictionary.
- **Strengths**: Concurrency via `ThreadPoolExecutor` speeds up network requests.
- **Weaknesses**: The HTML client downloads listing pages synchronously inside the thread worker. If a page download throws an exception, the thread fails, crashing the entire ETL run during `list(executor.map(...))`.
- **Risks**: Failure on a single partner page download causes loss of all scraped data.
- **Engineering Recommendation**: Catch network and parsing exceptions inside `process_partner`. Mark failed scrapes with `html_status = "Failed"` and store the error message in the dictionary instead of raising an exception.
- **Priority**: High
- **Impact**: High
- **Estimated Effort**: S

---

### Step 3: Merging and Stitches
- **Current Implementation**: The dictionaries are combined using a shallow merge: `merged = api_partner.copy(); merged.update(html_partner)`.
- **Strengths**: Extremely simple and fast.
- **Weaknesses**: If the API dictionary and HTML dictionary share common keys (e.g. `headquarters` or `rating`), the HTML dictionary value silently overwrites the API dictionary value without any warning or tracking.
- **Risks**: Data collision and loss of structured API information.
- **Engineering Recommendation**: Namespace keys scraped from HTML (e.g. prefixing HTML-derived fields with `html_` like `html_rating`, `html_headquarters`) or validate/select the preferred source explicitly during merge.
- **Priority**: Medium
- **Impact**: Medium
- **Estimated Effort**: S

---

### Step 4: Export Serialization
- **Current Implementation**: `ExportService` flattens dictionaries one level deep and outputs JSON/CSV. Lists are dumped as serialized JSON strings.
- **Strengths**: CSV flattening works for simple flat dictionary structures.
- **Weaknesses**: Shallow flattening fails for deeper nested structures (like `metadata.og` or `metadata.twitter`), leaving raw dictionaries in cells.
- **Risks**: Inconsistent formats in CSV columns, complicating downstream SQL analyses.
- **Engineering Recommendation**: Implement a recursive dictionary flattener that processes keys dynamically (e.g., `parent_child_subchild`) or enforce a strict export schema before writing CSVs.
- **Priority**: Medium
- **Impact**: High
- **Estimated Effort**: S
