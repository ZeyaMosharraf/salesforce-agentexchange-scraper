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