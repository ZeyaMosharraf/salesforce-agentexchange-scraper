# Salesforce AppExchange Partner Data Pipeline

An automated data pipeline that extracts, transforms, and enriches Salesforce AppExchange partner information into a comprehensive, structured dataset by combining Salesforce API responses with partner listing page data. The resulting dataset can support sales prospecting, partner discovery, market research, business intelligence, and other data-driven applications.

---

## 📖 Additional Documentation
For in-depth details about design patterns, code design, and output schemas, please refer to:
- 🏗 **[System Architecture](file:///g:/My Drive/Data Pipeline Code/Data Extraction/salesforce-agentexchange-scraper/docs/architecture.md)** — Architectural design, flow diagrams, and concurrency features.
- 📊 **[Data Dictionary](file:///g:/My Drive/Data Pipeline Code/Data Extraction/salesforce-agentexchange-scraper/docs/data_dictionary.md)** — Detailed descriptions of the output JSON/CSV fields and flattening logic.

---

## Overview

Salesforce AppExchange hosts thousands of consulting partners, independent software vendors (ISVs), and implementation partners across different industries and regions. While partner information is publicly available, it is distributed across Salesforce API responses and individual partner listing pages, making large-scale data collection difficult.

This project automates the complete data collection process by extracting partner records from the Salesforce AppExchange API, enriching them with additional information from each partner's listing page, and transforming the combined data into a structured dataset. The result is a centralized and reusable data source that can be used for sales prospecting, partner discovery, market research, competitive analysis, CRM enrichment, and business intelligence.

## Why I Built This

Salesforce AppExchange contains valuable information about consulting partners, implementation partners, and ISVs. However, obtaining this information at scale is challenging because the available data is fragmented across multiple sources.

The Salesforce API provides structured partner information such as company details, ratings, certifications, projects, and expertise. However, additional business information is only available within each partner's individual listing page as HTML content.

Collecting this information manually for hundreds or thousands of partners is inefficient, time-consuming, and difficult to maintain. Existing approaches often focus only on API extraction or HTML scraping, resulting in incomplete datasets.

To address this problem, this project was designed as a unified data pipeline that combines structured API data with additional information extracted from partner listing pages, producing a single, enriched dataset that can be reused for sales prospecting, partner research, CRM enrichment, competitive analysis, and business intelligence.

## Project Objectives

The primary objective of this project is to build a maintainable and production-oriented data pipeline for Salesforce AppExchange partner data by automating the complete data collection workflow.

The pipeline is designed to:
- Extract partner records from the Salesforce AppExchange API.
- Handle dynamic pagination to retrieve all available partner records.
- Transform nested API responses into structured business objects.
- Enrich partner records with additional information extracted from partner listing pages.
- Merge data collected from multiple sources into a single unified dataset.
- Export clean and analytics-ready datasets in multiple formats.
- Provide a modular architecture that is easy to extend, maintain, and integrate with future data workflows.

## Engineering Challenges

Building this pipeline involved significantly more than sending a simple API request. One of the biggest challenges was understanding how Salesforce AppExchange communicates with its backend services, as there is no publicly documented API available for this use case.

During development, several technical challenges had to be investigated and solved:
- **Reverse Engineered API**: Reverse engineered the Salesforce AppExchange network requests using browser developer tools to identify the correct API endpoint and request payload.
- **Nested JSON Deserialization**: Analyzed complex nested API responses where the primary payload was returned as a serialized JSON string (`returnValue`) that required additional parsing before processing.
- **Dynamic Pagination Strategy**: Designed a dynamic extraction strategy after discovering that traditional offset-based pagination was not reliable for retrieving the complete dataset.
- **Connection Pools & Retries**: Built retry mechanisms and error handling to improve stability against temporary network failures and server-side errors.
- **Concurrency**: Handled the extraction of hundreds of listing pages concurrently using a thread pool to avoid bottlenecking.

## Solution Architecture

The project follows a modular Extract → Transform → Enrich → Export workflow, where each stage has a single responsibility. This architecture improves maintainability, simplifies debugging, and allows individual components to evolve independently as business requirements change.

```text
                  Salesforce AppExchange
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
  Parse & Flatten API Data             Download Partner Pages
         │                                       │
         └───────────────────┬───────────────────┘
                             ▼
                  HTML Data Extraction
                             │
                             ▼
                   Data Enrichment & Merge
                             │
                             ▼
                  Structured Partner Dataset
                             │
                             ▼
                     Export Service
                 ┌───────────┴───────────┐
                 ▼                       ▼
               JSON                     CSV
                                         │
                                         ▼
                             ┌───────────┼────────────────────────┐
                           Sales │ CRM │ Analytics │ Market Research
```

---

## Core Features

- **🔍 Reverse Engineered API Integration**: Identified and analyzed the internal Salesforce AppExchange API through browser network inspection.
- **📥 Automated Data Extraction**: Dynamically extracts Salesforce AppExchange partner records, supporting automatic pagination.
- **🌐 HTML Data Enrichment**: Visits each partner listing page automatically, extracting additional business information.
- **🔄 Data Transformation**: Parses serialized API responses and flattens nested JSON objects into structured records.
- **🏗 Modular Architecture**: Clear separation of Clients, Services, Models, Configuration, and Utilities.
- **📝 Centralized Logging**: Structured logging across extraction and processing stages.
- **🔁 Fault Tolerant Requests**: Automatic retry mechanism for transient HTTP failures with configurable timeouts.
- **📤 Flexible Export**: Supports exporting processed data into JSON and CSV formats.

---

## Project Structure

The project has been refactored into a standardized modular architecture:

```text
salesforce-app-exchange-partner-pipeline/
│
├── docs/
│   ├── architecture.md           # Deep dive into system architecture and data flows
│   └── data_dictionary.md        # Reference guide for JSON/CSV schemas
│
├── src/
│   ├── clients/
│   │   ├── __init__.py           # Package exports for HTTP clients
│   │   ├── html_client.py        # Client for downloading partner pages
│   │   └── salesforce_client.py  # Client for calling the Salesforce search API
│   │
│   ├── config/
│   │   ├── __init__.py           # Package exports for settings
│   │   └── settings.py           # Application environment configuration
│   │
│   ├── models/
│   │   ├── __init__.py           # Package exports for data filters
│   │   └── partner_filter.py     # Models API search criteria and payload builder
│   │
│   ├── orchestrator/
│   │   ├── __init__.py           # Package exports for orchestrator
│   │   └── pipeline.py           # Main ETL pipeline coordinator
│   │
│   ├── services/
│   │   ├── __init__.py           # Package exports for core services
│   │   ├── export_service.py     # Service for writing JSON and CSV outputs
│   │   ├── extraction_service.py # Service for paginated API extraction
│   │   └── transformation_service.py # Service coordinating multi-threaded HTML scrapers
│   │
│   ├── transformations/
│   │   ├── __init__.py           # Package exports for data transformers
│   │   ├── html_transformation.py # Parses partner listing pages using BeautifulSoup
│   │   ├── merge_transformation.py # Combines API and scraped HTML dictionaries
│   │   └── partner_transformation.py # Extracts and flattens API partner records
│   │
│   ├── utils/
│   │   ├── __init__.py           # Package exports for logger
│   │   └── logger.py             # Setup configurations for application logger
│   │
│   └── main.py                   # Application entry point
│
├── output/
│   ├── partners.csv              # Enriched tabular partner dataset
│   └── partners.json             # Full nested JSON partner dataset
│
├── .env                          # Local environment variables
├── .gitignore                    # Git file exclusion rules
├── pyproject.toml                # Project configurations & dependency declarations
├── requirements.txt              # Standard python requirements file
└── README.md                     # Main project readme
```

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/salesforce-app-exchange-partner-pipeline.git
cd salesforce-app-exchange-partner-pipeline
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

### 3. Activate the Virtual Environment

**Windows**

```bash
.venv\Scripts\activate
```

**macOS / Linux**

```bash
source .venv/bin/activate
```

### 4. Install Dependencies

You can install dependencies using either the standard requirements file:

```bash
pip install -r requirements.txt
```

Or directly via `pyproject.toml` (which supports editable installs):

```bash
pip install -e .
```

---

## Running the Pipeline

Before running, make sure you copy the environment file example or create a `.env` file containing:

```env
API_URL=https://findpartners.salesforce.com/webruntime/api/apex/execute?language=en-US&asGuest=true&htmlEncode=false
REQUEST_TIMEOUT=30
```

Execute the pipeline from the project root:

```bash
python -m src.main
```

Logs will output details of the pagination offsets, concurrent listing scrapes, and final data exports. Outputs will be written directly to `output/partners.json` and `output/partners.csv`.