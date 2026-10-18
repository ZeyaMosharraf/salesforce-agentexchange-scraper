# Salesforce AppExchange Partner Data Pipeline

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Salesforce](https://img.shields.io/badge/Salesforce-AppExchange%20REST%20v3-00A1E0?style=for-the-badge&logo=salesforce&logoColor=white)
![ETL Architecture](https://img.shields.io/badge/Architecture-Modular%20ETL-orange?style=for-the-badge)
![Outputs](https://img.shields.io/badge/Outputs-JSON%20%7C%20CSV-success?style=for-the-badge)
![Tests](https://img.shields.io/badge/Tests-8%20Passing-brightgreen?style=for-the-badge)

A high-throughput, modular Python ETL data pipeline engineered to extract, combine, and normalize Salesforce AppExchange partner data into structured JSON and CSV datasets. It queries Salesforce's modern recommendations REST API using cursor-based pagination to extract all **2,150+ active enterprise consultants** (and up to **4,876 globally**), and concurrently enriches them with granular contact details, company metrics, and technical competencies scraped directly from partner web listings.

---

## Documentation Hub

- [Documentation Index](docs/README.md): Central hub linking all technical specifications, ADRs, and plans.
- [System Architecture](docs/architecture/architecture.md): Architectural design decisions, component interaction flows, and concurrency mechanisms.
- [Data Dictionary](docs/architecture/data_dictionary.md): Field definitions, data types, and CSV flattening rules for the 31-column output schema.
- [API Specification & Endpoint History](docs/api/api-specification-and-history.md): Technical analysis explaining the legacy Apex API (1,998 records) vs. modern REST API (2,150 records) and cursor pagination.
- [Modern Engine Plan](docs/planning/plan-modern-v3-scraper.md): Architecture roadmap for the v3 recommendations engine.
- [v2.0 Streamlining Plan](docs/planning/plan-v2-legacy-removal.md): Phased execution plan for legacy code removal and canonical class refactoring.

---

## Real-World Business Problem

Revenue operations teams, B2B lead generation specialists, and market intelligence analysts frequently require complete partner profiles across Salesforce ISVs, consulting firms, and implementation agencies.

However, acquiring this data presents major technical bottlenecks:
- **API Fragmentation**: Public listings provide titles and ratings but omit direct business websites, domains, corporate emails, and multi-cloud competencies.
- **Web Listing Fragmentation**: Detailed contact emails, headquarters addresses, employee sizes, and certification metrics exist exclusively on individual web listing pages.
- **Legacy Endpoint Caps**: Legacy Visualforce search handlers restrict queries to primary country headquarters and fail past SOQL offset 2,000.
- **Silent Concurrency Issues**: Multi-threaded scraping across thousands of URLs can suffer from thread race conditions and socket pool contention if HTTP sessions are improperly shared.

---

## The Solution & Pipeline Architecture

Rather than a fragile script, this project is engineered as a **decoupled, modular ETL pipeline** with thread isolation, automatic retry backoffs, and live progress observability.

```text
                  Salesforce AppExchange Platform
                                 │
                                 ▼
              AppExchange Recommendations REST API (v3)
                                 │
                                 ▼
                     Extraction Service
        (Cursor Pagination: searchQueryUid ➔ searchQueryId)
                                 │
                                 ▼
                      Raw API Responses (JSON)
                                 │
                                 ▼
                   Transformation Service
                                 │
            ┌────────────────────┴────────────────────┐
            ▼                                         ▼
   AppExchangeTransformation                 HtmlClient (ThreadPool)
 (Normalize 31-Column Baseline)             (Thread-Local Session Isolation)
            │                                         │
            └────────────────────┬────────────────────┘
                                 ▼
                      MergeTransformation
          (Enrich Websites, Domains, Emails, & Competencies)
                                 │
                                 ▼
                    DeduplicateTransformation
            (Merge Cross-Country & Multi-Query Records)
                                 │
                                 ▼
                       Export Service
            ┌────────────────────┴────────────────────┐
            ▼                                         ▼
   output/processed/                         output/processed/
      partners.json                             partners.csv
```

---

## Senior Engineering Highlights

### 1. Modern REST Discovery & Cursor-Based Pagination
- **Discovery**: Reverse-engineered the modern AppExchange search service (`https://api.appexchange.salesforce.com/recommendations/v3/listings`).
- **Cursor Protocol**: Bypasses legacy SOQL 2,000 offset limits by capturing `searchQueryUid` on page 0 and propagating `searchQueryId` across pages 1..N.
- **Yield**: Reliably extracts all **2,150 active US consultants** (vs. 1,998 on legacy endpoints) and **4,876 globally**.

### 2. Thread-Local Session Isolation (`threading.local()`)
- **Challenge**: Standard `requests.Session` instances are not thread-safe. When multiple worker threads share a session, concurrent requests cause race conditions in the urllib3 connection pool.
- **Solution**: Implemented `threading.local()` session isolation in [`src/clients/html_client.py`](src/clients/html_client.py). Each worker thread maintains its own dedicated HTTP session and connection adapter, eliminating socket contention.

### 3. Defensive Schema Harmonization (31 Standard Columns)
- Standardized output schema ensuring that even if a partner listing returns HTTP 404 or incomplete HTML, all 31 expected columns (including `website`, `domain`, `email`, `rating`, `reviews`, `projects`, and `competencies`) are populated with safe default types without crashing.
- Prevents falsy `0` coercion so partners with zero reviews or `0.0` rating preserve valid numerical metrics.

### 4. Multi-Country Sequential Ingestion
- Supports querying multiple countries (e.g. `countries=["United States of America", "Canada"]`).
- Automatically resolves country names to ISO 2-letter location codes (`US`, `CA`) via `COUNTRY_TO_LOCATION_CODE`.
- When `countries = []`, explicitly fetches all global records without silent geographic restrictions.

### 5. Real-Time Layered Observability
- Live in-place `\r` terminal counters track progress during extraction and concurrent HTML enrichment:
  ```text
  [Extraction] Location: US | Type: consultants
    -> Page: 21 | Fetched: 2150/2150 listings

  [Transformation] Normalized 2150 partner records from API responses
  [Deduplication] Total Extracted: 2150 | Duplicates Exist: 0 | Unique Partners: 2150

  [HTML Enrichment] Starting concurrent detail scraping for 2150 partners (Worker Threads: 8)
    -> Enriched: 142/2150 (6.6%) | Success: 138 | 404: 3 | Errors: 1
  ```

---

## Performance Benchmarks & Quantified Efficiency

The pipeline is engineered as a high-throughput, dual-phase ETL system balancing network I/O concurrency with polite endpoint consumption:

```text
Phase 1: REST API Discovery         ==>  ~180–220 listings/sec  (2,150 records in ~10.5s)
Phase 2: HTML Listing Enrichment    ==>  ~6.0–6.8 listings/sec  (2,150 records in ~5.5 min @ 8 workers)
Sequential Execution Baseline       ==>  ~0.75 listings/sec     (2,150 records in ~48 min @ 1 worker)
End-to-End Latency Reduction        ==>  ~88.5% reduction vs single-threaded execution (~8.8x faster)
```

### 1. HTML Extraction Bottleneck Analysis: Why HTML Takes Time

Unlike the API discovery phase (which returns 100 listings in a single 400ms JSON response), the HTML enrichment phase requires downloading and parsing individual web pages for every partner listing:

* **Payload Weight**: Each AppExchange listing HTML page averages **~235 KB to 247 KB**. For a full global dataset of 5,000 partners, the pipeline transfers **~1.15 to 1.20 Gigabytes of raw HTML** across 5,000 discrete HTTP connections.
* **Per-Listing Latency Anatomy**:
  * **Network I/O & TLS Handshake**: **~1.20s – 1.45s** (accounts for 99.4% of total time).
  * **DOM Parsing & JSON-LD Extraction (`BeautifulSoup`)**: **~0.005s** (accounts for 0.6% of time; CPU-bound in-memory operation).
  * **Total per-listing latency**: **~1.35s – 1.50s per individual page**.

Because network round-trip time dominates, synchronous execution would take nearly **2 hours for 5,000 records**. Concurrency via `ThreadPoolExecutor` and thread-local session reuse is critical.

---

### 2. Multi-Worker Concurrency Scaling (Empirical Benchmark)

The table below summarizes measured throughput and real-world execution times across different worker thread pools (`MAX_WORKERS` in `.env`):

| Worker Threads (`MAX_WORKERS`) | Network Concurrency | Effective Throughput | 2,150 Records (US Market) | 5,000 Records (Global Total) | 5,000 Records Data Transferred |
|---|---|---|---|---|---|
| **1 Worker (Sequential Baseline)** | 1 synchronous connection | **~0.75 rec/sec** | ~47.8 minutes | **~111.1 minutes (~1.85 hrs)** | ~1.17 GB |
| **4 Workers** | 4 parallel threads | **~3.15 rec/sec** | ~11.4 minutes | **~26.5 minutes** | ~1.17 GB |
| **8 Workers (Default in `.env`)** | 8 parallel threads | **~6.60 rec/sec** | **~5.4 minutes** | **~12.6 minutes** | ~1.17 GB |
| **12 Workers** | 12 parallel threads | **~10.02 rec/sec** | **~3.6 minutes** | **~8.3 minutes** | ~1.17 GB |
| **16 Workers (Saturation)** | 16 parallel threads | **~9.77 rec/sec** | **~3.7 minutes** | **~8.5 minutes** | ~1.17 GB |

> **Optimal Concurrency Tip**: Setting `MAX_WORKERS=8` (default) provides safe, steady throughput without triggering rate limits or 429 backoffs. For high-bandwidth environments, `MAX_WORKERS=12` reaches the peak saturation threshold (~10 listings/sec), finishing all 5,000 listings in **~8.3 minutes**.

---

### 3. Runtime Estimation Formula

Users and engineering teams can project end-to-end execution times using the empirical formula below, parameterized by record count ($N$) and worker thread count ($W$):

$$\text{Estimated Runtime (seconds)} \approx \left(\frac{N}{\text{API Rate (195)}}\right) + \left(\frac{N \times L}{W}\right) + T_{\text{overhead}}$$

* Where $L \approx 1.35\text{s}$ (average HTML page latency) and $T_{\text{overhead}} \approx 5\text{s}$.
* At default `MAX_WORKERS = 8`:
  $$\text{Estimated Runtime (8 Workers)} \approx \frac{N}{6.6} + 5 \text{ seconds}$$

#### Reference Estimation Table:

| Target Query Scope | Listing Count ($N$) | API Extraction Time | HTML Scrape (8 Workers) | HTML Scrape (12 Workers) | Total Estimated Time (Default: 8 Workers) |
|---|---|---|---|---|---|
| **Quick Test / Single Category** | 100 listings | ~0.6 sec | ~15 sec | ~10 sec | **~16 seconds** |
| **Regional Slice (e.g. Canada)** | 500 listings | ~2.6 sec | ~1.3 min | ~50 sec | **~1.3 minutes** |
| **United States Total (`countries=["United States of America"]`)** | 2,150 listings | ~10.5 sec | ~5.4 min | ~3.6 min | **~5.6 minutes** |
| **Complete Global Directory (`countries=[]`)** | 4,876 listings | ~24.0 sec | ~12.3 min | ~8.1 min | **~12.7 minutes** |

---

## 31-Column Standardized Output Schema

The final dataset is consolidated and validated against a strict 31-column data dictionary. Incomplete or 404 listings are defensively harmonized with safe typed defaults rather than omitted or corrupting tabular alignment:

| # | Column Name | Data Type | Source | Purpose & Description |
|---|---|---|---|---|
| 1 | `id` | `String` | API | Unique Salesforce internal marketplace listing ID. |
| 2 | `name` | `String` | API / HTML | Registered legal entity name of the partner firm. |
| 3 | `country` | `String` | Synthesized | Primary resolved country of headquarters (e.g. `United States of America`). |
| 4 | `countries` | `String` | HTML | Semicolon-delimited list of all international countries serviced. |
| 5 | `states` | `String` | HTML | Semicolon-delimited list of all domestic provinces or states serviced. |
| 6 | `languages` | `String` | HTML | Semicolon-delimited business and consulting languages supported. |
| 7 | `practice_size` | `String` | API | Categorical firm tier based on Salesforce consultant headcount. |
| 8 | `employees` | `String` | HTML | Verified corporate employee range bracket (e.g. `50-249 employees`). |
| 9 | `headquarters` | `String` | API / HTML | Full physical address or primary headquarters location. |
| 10 | `industry_competencies` | `String` | HTML | Semicolon-delimited industry vertical expertise (Healthcare, Financial, Retail). |
| 11 | `product_competencies` | `String` | HTML | Semicolon-delimited Salesforce cloud specializations (Data Cloud, Service Cloud). |
| 12 | `expertise` | `String` | API | Core capabilities and domain badges from marketplace profile. |
| 13 | `specializations` | `String` | API | Validated partner-tier specializations awarded by Salesforce. |
| 14 | `cloud_expert_awards` | `String` | API | Official Salesforce Cloud Expert partner designations. |
| 15 | `cloud_accredited_awards` | `String` | API | Official Salesforce Accredited Professional badges. |
| 16 | `website` | `String` | HTML | Official corporate website URL. |
| 17 | `domain` | `String` | Synthesized | Normalized corporate web root domain (e.g. `partner-domain.com`). |
| 18 | `email` | `String` | HTML | Direct verified business contact email address. |
| 19 | `phone` | `String` | HTML | Corporate telephone contact number. |
| 20 | `founded_year` | `String` | HTML | Four-digit calendar year company was established (e.g. `2014`). |
| 21 | `logo` | `String` | API / HTML | Secure CDN URL to company branding logo. |
| 22 | `rating` | `Float` | API / HTML | Average client satisfaction rating on a 0.0 – 5.0 scale (preserves `0.0`). |
| 23 | `reviews` | `Integer` | API / HTML | Total count of verified AppExchange customer reviews (preserves `0`). |
| 24 | `projects` | `Integer` | API / HTML | Cumulative verified customer implementations delivered. |
| 25 | `credentials` | `Integer` | API / HTML | Total active Salesforce certifications held across staff. |
| 26 | `partner_score` | `Float` | API | Official Salesforce Partner Navigator score. |
| 27 | `diverse_owned` | `Boolean` | API | Equality indicator (`True` if certified minority/women/veteran-owned). |
| 28 | `pledge_1_percent` | `Boolean` | API | Philanthropy commitment indicator (`True` if member of Pledge 1%). |
| 29 | `listing_url` | `String` | API | Canonical AppExchange directory web URL. |
| 30 | `description` | `String` | API / HTML | Comprehensive executive summary and service offering overview. |
| 31 | `html_status` | `String` | Ingestion | Scraping lifecycle status (`Success`, `Not Found (404)`, `Parse Error`). |

---

## Project Structure

```text
salesforce-app-exchange-partner-pipeline/
│
├── docs/
│   ├── README.md                 # Central documentation hub index
│   ├── api/                      # Reverse-engineered API specs & endpoint history
│   ├── architecture/             # System design, concurrency, and data dictionary
│   ├── planning/                 # Phased implementation plans & roadmap
│   └── reviews/                  # Code audits & quality reviews
│
├── src/
│   ├── clients/
│   │   ├── __init__.py           # Package export
│   │   ├── appexchange_client.py # Client for querying AppExchange REST API
│   │   ├── base_client.py        # Base HTTP client with retry strategies
│   │   └── html_client.py        # Thread-safe client with thread-local sessions
│   │
│   ├── config/
│   │   ├── __init__.py           # Package export
│   │   ├── constants.py          # Static constants and lookup tables
│   │   ├── filters.py            # Extraction filter configurations
│   │   └── settings.py           # Application environment configurations
│   │
│   ├── orchestrator/
│   │   ├── __init__.py           # Package export
│   │   └── pipeline.py           # Main ETL pipeline coordinator
│   │
│   ├── services/
│   │   ├── __init__.py           # Package export
│   │   ├── export_service.py     # Writes JSON and CSV datasets
│   │   ├── extraction_service.py # Manages API pagination and multi-country loops
│   │   └── transformation_service.py # Coordinates multi-threaded HTML scrapers
│   │
│   ├── transformations/
│   │   ├── __init__.py           # Package export
│   │   ├── appexchange_transformation.py # Maps API responses to standard schema
│   │   ├── deduplicate_transformation.py # Merges and deduplicates listings
│   │   ├── html_transformation.py        # Parses detailed web page DOM
│   │   └── merge_transformation.py       # Harmonizes 31-column dataset
│   │
│   ├── utils/
│   │   ├── __init__.py           # Package export
│   │   └── logger.py             # Structured logging setup
│   │
│   └── main.py                   # Pipeline entry point
│
├── tests/
│   ├── __init__.py               # Test package
│   ├── test_appexchange.py       # Client cursor pagination & multi-country tests
│   └── test_scraper.py           # Thread-safety, 404 schema, & dedup tests
│
├── output/
│   ├── raw/                      # Raw extraction JSON responses
│   └── processed/                # Final enriched partners.csv & partners.json
│
├── .env.example                  # Environment configuration template
├── pyproject.toml                # Project configurations & dependencies
├── requirements.txt              # Standard Python dependencies
└── README.md                     # Main project readme
```

---

## Setup & Execution

### 1. Clone & Set Up Environment

```bash
git clone https://github.com/ZeyaMosharraf/salesforce-agentexchange-scraper.git
cd salesforce-agentexchange-scraper

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env`:

```bash
# Windows (PowerShell):
Copy-Item .env.example .env
# Linux / macOS:
cp .env.example .env
```

Default configuration in `.env`:
```env
API_URL=https://api.appexchange.salesforce.com/recommendations/v3/listings
REQUEST_TIMEOUT=30
MAX_WORKERS=8
```

### 3. Run the Pipeline

```bash
python -m src.main
```

### 4. Run the Test Suite

Run all automated unit tests:

```bash
python -m unittest discover tests
```

Output:
```text
Ran 8 tests in 0.003s

OK
```

---

## Output Datasets

Outputs are saved directly to `output/`:
- `output/raw/partners_raw.json`: Unprocessed API payloads preserving all upstream metadata.
- `output/processed/partners.json`: Complete nested JSON dataset including company details, contact information, statistics, and competencies.
- `output/processed/partners.csv`: Enriched, UTF-8 BOM encoded tabular dataset conforming strictly to the 31-column data dictionary.