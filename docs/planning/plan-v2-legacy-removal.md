# Phase Plan: Legacy Code Removal & v2.0 Architecture Streamlining

## 1. Overview & Context

With the `v1.0.0` release published on GitHub, the legacy Visualforce/Apex Remoting pipeline (`findpartners.salesforce.com`) is permanently preserved in git history and release archives.

This phase streamlines the codebase for **v2.0.0**:
- Removes obsolete Apex client, filter models, and transformation files.
- Adopts canonical naming (`AppExchangeClient`, `AppExchangeTransformation`) without temporary prefixes.
- Simplifies configuration so users only configure intuitive filters (`countries`, `listing_type`, `page_size`).
- Implements sequential multi-country extraction loops.

---

## 2. Locked Decisions

| Decision Area | Selected Strategy | Rationale |
| :--- | :--- | :--- |
| **Class & Module Naming** | Canonical (`AppExchangeClient`, `AppExchangeTransformation`) | The modern REST API is now the sole production engine; removing "v3" or "modern" prefixes yields clean, standard architecture. |
| **Country Filtering** | Multi-Country Sequential Loop | If a user specifies `["United States of America", "Canada"]`, the engine queries `location=US` (2,150) then `location=CA`, aggregating both datasets seamlessly. |
| **Legacy Codebase** | Clean Removal | Remove `salesforce_client.py`, `partner_filter.py`, and `partner_transformation.py` entirely. Preserved in `v1.0.0` tag. |
| **Settings & Env** | Single `API_URL` pointing to Recommendations v3 | Removes dead `DATA_SOURCE` and legacy Apex endpoint URLs from `.env.example` and `settings.py`. |

---

## 3. Phased Execution Steps

### Phase 1: Configuration & Settings Simplification
- **File**: `src/config/settings.py`
  - Update `api_url` to `https://api.appexchange.salesforce.com/recommendations/v3/listings`.
  - Remove `DATA_SOURCE` and `modern_api_url`.
- **File**: `src/config/filters.py`
  - Clean up `FilterConfig`: keep `countries`, `listing_type`, `page_size`.
  - Retain `COUNTRY_TO_LOCATION_CODE` dictionary for automatic mapping.
- **File**: `.env.example`
  - Remove legacy Apex `API_URL` and `DATA_SOURCE` toggle. Document clean modern variables.

### Phase 2: Canonical Client & Transformation Promotion
- **File**: `src/clients/appexchange_client.py` (promoted from `appexchange_v3_client.py`)
  - Class: `AppExchangeClient`.
- **File**: `src/clients/__init__.py`
  - Export `AppExchangeClient`, `HtmlClient`, `BaseClient`.
  - Remove `SalesforceClient`.
- **File**: `src/transformations/appexchange_transformation.py` (promoted from `appexchange_v3_transformation.py`)
  - Class: `AppExchangeTransformation`.
- **File**: `src/transformations/__init__.py`
  - Export `AppExchangeTransformation`, `HtmlTransformation`, `MergeTransformation`, `DeduplicateTransformation`.
  - Remove `PartnerTransformation`.

### Phase 3: Obsolete Legacy Deletion
- Delete:
  - `src/clients/salesforce_client.py`
  - `src/models/partner_filter.py`
  - `src/models/__init__.py` (and remove `src/models/` if empty)
  - `src/transformations/partner_transformation.py`

### Phase 4: Service Layer Refactoring
- **File**: `src/services/extraction_service.py`
  - Replace dual-engine conditional branching with pure `AppExchangeClient`.
  - Implement clean loop across `filter_config.countries` resolving 2-letter location codes.
- **File**: `src/services/transformation_service.py`
  - Remove legacy detection logic; directly use `AppExchangeTransformation`.

### Phase 5: Test Suite Modernization & Verification
- **Files**: `tests/test_scraper.py`, `tests/test_appexchange.py`
  - Consolidate tests into canonical names (`AppExchangeClient`, `AppExchangeTransformation`).
  - Verify multi-country iteration, cursor pagination, 31-column schema validation, and thread safety.
  - Run full test suite to guarantee 100% pass rate.

