# Salesforce Partner Extraction API Specification & Evolution History

## Overview

This document provides a technical specification of the internal APIs used by Salesforce to power partner and consultant discovery across its marketplaces. It details the legacy **Lightning WebRuntime Apex Gateway** (`findpartners.salesforce.com`) and the modern **AppExchange Search & Discovery REST API** (`api.appexchange.salesforce.com`), explaining their architectures, schemas, pagination behaviors, and the historical discrepancy between the 1,998 and 2,150 consultant counts.

---

## 1. System Comparison Matrix

| Feature | Legacy PartnerFinder Gateway | Modern AppExchange Discovery API |
| :--- | :--- | :--- |
| **Marketplace Host** | `findpartners.salesforce.com` | `appexchange.salesforce.com/consulting` |
| **API Endpoint** | `/webruntime/api/apex/execute` | `/recommendations/v3/listings` |
| **Protocol** | HTTP `POST` (Apex JSON RPC) | HTTP `GET` (RESTful JSON) |
| **Underlying Engine** | Direct SOQL over `Partner__c` | Search & Discovery index (Data Cloud / Coveo hybrid) |
| **Active Status** | Legacy (under maintenance) | Active / Production (powers modern Web UI) |
| **US Consultants Count** | **1,998** | **2,150** |
| **Canada Consultants Count**| **524** | **616** |
| **Total Global Consultants**| **4,796** | **4,876** |
| **Pagination Mode** | Integer page index (`offset: 0, 1, 2...`) | Cursor-based (`searchQueryId` + `page`) |
| **Hard Database Limits** | SOQL `OFFSET 2000` limit | None (standard REST pagination up to 200/page) |
| **Authentication** | Public Guest Access (`asGuest=true`) | Public Client Access (`Origin: appexchange.salesforce.com`) |

---

## 2. API 1: Legacy PartnerFinder Apex API

### Overview

This endpoint is part of the Salesforce Experience Cloud (WebRuntime) framework powering the legacy Partner Finder tool. It acts as an RPC gateway executing Apex classes exposed to guest users.

### Endpoint Details

- **URL**: `https://findpartners.salesforce.com/webruntime/api/apex/execute?language=en-US&asGuest=true&htmlEncode=false`
- **Method**: `POST`
- **Headers**:

  ```http
  Content-Type: application/json
  Origin: https://appexchange.salesforce.com
  Referer: https://appexchange.salesforce.com/
  User-Agent: Mozilla/5.0 ...
  ```

### Apex Controller & Method

- **Apex Class**: `@udd/01p3m00000EBlzK`
- **Target Method**: `getPartners`
- **Secondary Method**: `getFilterOptions` (returns filter taxonomies)

### Request Payload

```json
{
  "namespace": "",
  "classname": "@udd/01p3m00000EBlzK",
  "method": "getPartners",
  "isContinuation": false,
  "params": {
    "selectedFiltersFromJS": {
      "countries": ["United States of America"],
      "states": [],
      "practiceSize": [],
      "expertises": [],
      "specializations": [],
      "rating": null,
      "impactFilters": {},
      "sortedBy": "expertise",
      "offset": 0,
      "limitSize": 500,
      "fromFinder": false
    }
  },
  "cacheable": false
}
```

### Response Payload Structure

```json
{
  "status": 200,
  "returnValue": {
    "isSuccess": true,
    "results": {
      "numPartners": 1998,
      "locationSelected": true,
      "partners": [
        {
          "partner": {
            "Id": "a7f3m000000PTxrAAG",
            "Name": "Ascend Technologies",
            "AppExchange_Rating__c": 4.93,
            "Headquarters__c": "Chicago, IL",
            "AppExchange_Listing_URL__c": "https://appexchange.salesforce.com/appxConsultingListingDetail?listingId=a0N3u00000MBkqUEAT",
            "Number_of_Projects__c": 25,
            "Number_of_Credentials__c": 38,
            "PF_Total_Score__c": 1190.8
          },
          "expertises": [...],
          "specializations": [...]
        }
      ]
    }
  }
}
```

### Known Architectural Limitations

1. **Strict Literal Matching**: Searches strictly against the database field `Partner__c.Country__c`. Multi-region partners that do not have `"United States of America"` as their primary database headquarters are excluded.
2. **Salesforce SOQL Offset Limit**: If a query returns more than 2,000 records, the Apex controller attempts to run `OFFSET 2000`, which raises:
   `Maximum SOQL offset allowed is 2000`.
3. **Delayed Synchronization**: As observed in the `getFilterOptions` response, this service carries an active notice:
   > *"Partner Finder is currently under maintenance. Partner listings may not accurately reflect partner information and will be updated shortly."*

---

## 3. API 2: Modern AppExchange Search & Discovery REST API

### Modern Overview

This is the modern, cloud-native search and recommendation service that directly powers the search experience at `https://appexchange.salesforce.com/consulting`. It queries a consolidated search index that combines marketplace listings with multi-region delivery capabilities.

### Modern Endpoint Details

- **URL**: `https://api.appexchange.salesforce.com/recommendations/v3/listings`
- **Method**: `GET`
- **Headers**:

  ```http
  Origin: https://appexchange.salesforce.com
  Referer: https://appexchange.salesforce.com/
  User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
  ```

### Query Parameters

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `type` | String | Yes | Listing entity type (`consultants` for partners). |
| `location` | String | No | 2-letter ISO country code (`US`, `CA`, `GB`, `IN`, `DE`, `AU`). |
| `page` | Integer | Yes | Zero-indexed page number (`0, 1, 2...`). |
| `pageSize` | Integer | Yes | Batch size per response. Supports `12`, `50`, `100`, `200`. |
| `searchQueryId` | UUID | Conditional | **Required for all pages > 0**. Pass the `searchQueryUid` received from page `0`. |
| `language` | String | No | Marketplace locale (`en` by default). |
| `sponsoredCount`| Integer | No | Number of paid sponsored listings prepended (set to `0` to omit ads). |

### Country Code Mapping & Verified Counts

| Country Name | ISO Code (`location`) | Verified Search Index Count |
| :--- | :--- | :--- |
| United States | `US` | **2,150** |
| Canada | `CA` | **616** |
| United Kingdom | `GB` | **700** |
| India | `IN` | **1,312** |
| Germany | `DE` | **372** |
| Australia | `AU` | **405** |
| *All Global (Unfiltered)* | *(omitted)* | **4,876** |

### Cursor Pagination Protocol

To page through listings without duplicate drift or dropped items:

1. **Initial Page (Page 0)**:

   ```http
   GET /recommendations/v3/listings?type=consultants&location=US&page=0&pageSize=100&sponsoredCount=0
   ```

   **Response includes**:

   ```json
   {
     "totalCount": 2150,
     "searchQueryUid": "891a4e98-83ee-4d56-ab85-d2f5807d3895",
     "listings": [...]
   }
   ```

2. **Subsequent Pages (Page 1..N)**:
   Pass the returned `searchQueryUid` as the `searchQueryId` parameter:

   ```http
   GET /recommendations/v3/listings?type=consultants&location=US&page=1&pageSize=100&sponsoredCount=0&searchQueryId=891a4e98-83ee-4d56-ab85-d2f5807d3895
   ```

   *Note: Omitting `searchQueryId` on pages > 0 causes the server to reset to page 0 results.*

### Listing Object Schema

```json
{
  "oafId": "a0N30000009xKzhEAE",
  "type": "consultant",
  "title": "Coastal: #1 Salesforce Consulting; Implementation, Data, Integration, Snowflake",
  "description": "Coastal is the consultancy that makes you successful using Salesforce...",
  "listingCategories": [],
  "publisher": "Coastal",
  "logos": [
    {
      "mediaId": "https://appexchange.salesforce.com/image_host/f812db76-36f4-4633-b2b2-740fc3cc0b57.png",
      "logoType": "Logo",
      "external_id": "90ac4430-215c-44d0-a088-1eaca41763f7"
    }
  ],
  "averageRating": 4.95,
  "reviewsAmount": 560,
  "chatEnabled": false,
  "additionalProps": {
    "agentCount": 0,
    "topicCount": 0,
    "actionCount": 0,
    "agentDescription": "",
    "mcpServerCount": 0
  }
}
```

---

## 4. The 152 Consultant Discrepancy Analysis (1,998 vs. 2,150)

Why does the website display **2,150 results** while the legacy Apex API returned **1,998**?

1. **Multi-Region Consulting Capabilities**:
   - The modern AppExchange index evaluates both primary headquarters **and** registered consulting operational delivery regions (`consultantLocations`).
   - For example, an international consultancy headquartered in Toronto or London with a registered practice office in New York is indexed under `location=US` in the modern search index, but was omitted from the strict single-country `Country__c = 'United States of America'` field in the legacy PartnerFinder database.
2. **Index Refresh Cadence**:
   - The legacy PartnerFinder gateway reflects an asynchronous batch-replicated table subject to maintenance delays.
   - The modern AppExchange Search index is continuously updated as new listings pass review or are published on the marketplace.
3. **Delisted/Dormant Record Filtering**:
   - The modern discovery index suppresses inactive and delisted consultant listings, ensuring that URLs extracted from this index have a substantially lower rate of 404 responses.

---

## 5. Architectural Recommendations

1. **Extraction Service Strategy**:
   - Keep `SalesforceClient` as the legacy fallback client.
   - Implement an `AppExchangeDiscoveryClient` targeting `/recommendations/v3/listings` to extract the full 2,150 US partners and 616 Canadian partners.
2. **Standard Listing URL Resolution**:
   - Both APIs expose the standard listing ID:
     - Legacy: `partner.AppExchange_Listing_URL__c`
     - Modern: `https://appexchange.salesforce.com/appxListingDetail?listingId=` + `listing.oafId`
   - Both feed seamlessly into [`TransformationService`](file:///d:/Github%20Project/Data%20Scrapping/salesforce-agentexchange-scraper/src/services/transformation_service.py) for deep HTML parsing, metadata extraction, and multi-threaded enrichment.
