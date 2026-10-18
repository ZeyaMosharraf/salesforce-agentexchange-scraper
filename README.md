# Salesforce AppExchange Partner Data Pipeline

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Salesforce](https://img.shields.io/badge/Salesforce-AppExchange-00A1E0?style=for-the-badge&logo=salesforce&logoColor=white)
![ETL Architecture](https://img.shields.io/badge/Architecture-Modular%20ETL-orange?style=for-the-badge)
![Outputs](https://img.shields.io/badge/Outputs-JSON%20%7C%20CSV-success?style=for-the-badge)

A modular Python ETL data pipeline engineered to extract, combine, and normalize Salesforce AppExchange partner data into structured JSON and CSV datasets. It merges structured partner metadata from internal Salesforce APIs with granular contact information scraped concurrently from partner web pages.

---

## Documentation Links

- [System Architecture](docs/architecture/architecture.md): Architectural design decisions, component interaction flows, and concurrency mechanisms.
- [Data Dictionary](docs/architecture/data_dictionary.md): Field definitions, data types, and CSV flattening rules for the final output schemas.
- [API Specification & History](docs/api/api-specification-and-history.md): Deep-dive comparison between legacy Apex vs. modern AppExchange REST APIs.
- [Modern Engine Implementation Plan](docs/planning/plan-modern-v3-scraper.md): Phased roadmap to extract all 2,150 consultants.

---

## Real-World Business Problem

Sales & Revenue teams, B2B lead generation specialists, and market intelligence analysts frequently require complete partner profiles across Salesforce ISVs, consulting firms, and implementation agencies. 

However, acquiring this data presents a major technical bottleneck:
- **API Fragmentation**: The Salesforce API returns numerical metrics (ratings, certification counts, total project numbers, expertise tags) but excludes direct business contact details.
- **Web Listing Fragmentation**: Detailed contact emails, corporate phone numbers, street addresses, taglines, whitepaper resources, and employee sizes exist exclusively on individual web listing pages.
- **Manual Overhead**: Manually collecting data for thousands of partner firms across multiple web pages is inefficient, error-prone, and unsustainable.

---

## The Solution & Engineering Strategy

Rather than building a simple web scraper, this project was designed as a **decoupled, modular ETL pipeline**. It combines structured API extraction with concurrent web page parsing to build a single, unified, and enriched partner dataset.

```text
                  Salesforce AppExchange Platform
                                 │
                                 ▼
                      Salesforce Partner API
                                 │
                                 ▼
                       Extraction Service
                                 │
                                 ▼
                       Raw API Response (JSON)
                                 │
                                 ▼
                     Transformation Service
                                 │
             ┌───────────────────┴───────────────────┐
             │                                       │
             ▼                                       ▼
     Parse & Flatten API Data             Download Listing HTML
             │                                       │
             └───────────────────┬───────────────────┘
                                 ▼
                        HTML Data Extraction
                                 │
                                 ▼
                     Data Enrichment & Merge
                                 │
                                 ▼
                      Structured Partner Record
                                 │
                                 ▼
                         Export Service
                     ┌───────────┴───────────┐
                     ▼                       ▼
                   JSON                     CSV
```

---

## Logical Architecture & Senior Engineering Decisions

This pipeline was engineered with clear design trade-offs and production architectural principles:

### 1. Single Responsibility & Decoupled Architecture
- **Decision**: Separated API Clients (`clients/`), Data Transformations (`transformations/`), and Core Services (`services/`).
- **Logical Reasoning**: Isolating HTML parsing from HTTP retrieval ensures that if Salesforce updates a web page CSS class, the API extraction stage remains unaffected (Fault Isolation).

### 2. Managed Concurrency over Unbounded Fetching
- **Decision**: Implemented `ThreadPoolExecutor(max_workers=8)` for HTML listing page enrichment.
- **Logical Reasoning**: Bounded thread pooling speeds up network downloads by over 70% while protecting the pipeline against rate-limiting (HTTP 429) or IP bans from server-side firewalls.

### 3. Reverse-Engineering Private Endpoints
- **Decision**: Inspected browser network traffic to map internal Apex endpoints (`@udd/01p3m00000EBlzK` / `getPartners`).
- **Logical Reasoning**: Bypassed missing public API documentation by engineering custom dataclass payload builders (`PartnerFilter`) matching the exact payload schema required by Salesforce backend controllers.

### 4. Graceful Degradation for SOQL Offset Caps
- **Decision**: Intercepted Salesforce SOQL query caps at offset 2,000 (`Maximum SOQL offset allowed`).
- **Logical Reasoning**: Instead of allowing the program to throw an uncaught exception, the extraction service catches the limit error, logs a warning, and safely passes all previously extracted data to the transformation stage.

### 5. Defensive HTML Parsing & Schema Normalization
- **Decision**: Built safe extraction utilities (`_safe_text`, `_safe_attr`) with fallback selector cascades.
- **Logical Reasoning**: Prevents runtime `AttributeError` or `TypeError` crashes when parsing incomplete listing pages. Missing fields are normalized cleanly to empty strings or default fallback values.

---

## Key Pipeline Features

- **Automated API Extraction**: Downloads paginated partner listings directly from Salesforce internal API endpoints.
- **Concurrent Web Mining**: Concurrently scrapes HTML listing pages to pull public emails, websites, phone numbers, and physical addresses.
- **Data Serialization & Normalization**: Decodes nested string-encoded JSON payloads (`returnValue`) into structured Python dictionaries.
- **Fault-Tolerant Session Management**: Reusable HTTP sessions with `urllib3` exponential backoff retries for transient 50x and 429 response codes.
- **Multi-Format Data Export**: Generates both nested JSON files for high-fidelity storage and flattened CSV files (with UTF-8 BOM encoding) for spreadsheet analysis.

---

## Project Structure

```text
salesforce-app-exchange-partner-pipeline/
│
├── docs/
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
│   │   └── html_client.py        # Thread-safe client for downloading web pages
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
│   │   ├── extraction_service.py # Manages API pagination and extraction logic
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
├── output/
│   ├── partners.csv              # Enriched tabular CSV dataset
│   └── partners.json             # Full nested JSON dataset
│
├── .env                          # Local environment variables settings
├── .env.example                  # Template for environment variables
├── .gitignore                    # Files excluded from git
├── pyproject.toml                # Project configurations and dependency declarations
├── requirements.txt              # Standard Python dependencies
└── README.md                     # Main project readme
```

---

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/salesforce-app-exchange-partner-pipeline.git
cd salesforce-app-exchange-partner-pipeline
```

### 2. Create a Virtual Environment

**Windows**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

Using `requirements.txt`:
```bash
pip install -r requirements.txt
```

Or editable installation via `pyproject.toml`:
```bash
pip install -e .
```

---

## Execution & Output

### 1. Environment Settings

Copy `.env.example` to `.env` and configure as required:

**Windows (PowerShell)**
```powershell
Copy-Item .env.example .env
```

**macOS / Linux**
```bash
cp .env.example .env
```

Example configuration:

```env
API_URL=https://findpartners.salesforce.com/webruntime/api/apex/execute?language=en-US&asGuest=true&htmlEncode=false
REQUEST_TIMEOUT=30
USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
MAX_WORKERS=8
```

### 2. Run the Pipeline

Execute the pipeline from the project root:

```bash
python -m src.main
```

### 3. Generated Datasets

Execution logs will track pagination offsets and multi-threaded scraping progress. Final datasets are output directly to:
- `output/partners.json` (Full nested JSON dataset)
- `output/partners.csv` (Enriched tabular CSV dataset)