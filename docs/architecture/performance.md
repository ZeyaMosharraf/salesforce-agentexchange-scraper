# Performance Audit

This document reviews the performance bottlenecks, processing overhead, and network resource reuse of the Salesforce AppExchange Scraper.

---

### Network and Page Download Bottlenecks
- **Current Implementation**: The pipeline fetches each partner listing page over HTTP. Although this is done in a thread pool, every partner page requires a distinct GET request.
- **Strengths**: Concurrent downloads via `ThreadPoolExecutor` bypass synchronous blockages.
- **Weaknesses**: The HTML client downloads full page bodies. Listing pages contain heavy assets, scripts, stylesheets, and UI elements. Downloading the full raw HTML string wastes significant bandwidth and CPU time in HTML decoding.
- **Risks**: Heavy data usage and slower scrapes, exposing the crawler to potential rate-limiting.
- **Engineering Recommendation**: Use HTTP HEAD requests where possible to check if listing contents changed, or utilize compressed HTTP transfers (gzip/brotli), which requests handles automatically but should be checked. If listing page structures allow, extract data directly from JSON API data blocks embedded inside scripts rather than parsing the entire DOM.
- **Priority**: Medium
- **Impact**: High
- **Estimated Effort**: M

---

### HTML Parsing CPU Bottlenecks
- **Current Implementation**: `HtmlTransformation` uses `BeautifulSoup` with the `lxml` parser to extract details.
- **Strengths**: `lxml` is a C-based parser, making it significantly faster than Python's standard `html.parser`.
- **Weaknesses**: Creating a new BeautifulSoup DOM tree for every partner in every thread generates significant CPU overhead and memory allocations.
- **Risks**: High CPU utilization on multi-core systems, possibly hitting Python's Global Interpreter Lock (GIL) limits because part of the BeautifulSoup object initialization is CPU-heavy.
- **Engineering Recommendation**: Avoid parsing the entire DOM if the data is available in a script block. For example, if the partner listing details are embedded in a `<script>` tag as JSON, extract the script tag via simple regex or selective parsing, parse the JSON string, and bypass the hundreds of CSS selector queries.
- **Priority**: High
- **Impact**: High
- **Estimated Effort**: M

---

### JSON/CSV Serialization Overhead
- **Current Implementation**: `ExportService` flattens data and exports using `pandas.DataFrame.to_csv`.
- **Strengths**: Simple file export. Pandas efficiently handles tabular exports.
- **Weaknesses**: Instantiating a Pandas DataFrame for thousands of dictionaries in-memory consumes significant RAM.
- **Risks**: Out-of-memory (OOM) failures when running the scraper for very large partner directories on resource-constrained containers.
- **Engineering Recommendation**: Use Python's built-in `csv` module (`csv.DictWriter`) or stream-based JSON/CSV writers to export data iteratively as it is transformed, rather than holding the entire dataset in memory and converting it using Pandas.
- **Priority**: Medium
- **Impact**: Medium
- **Estimated Effort**: S
