# Salesforce AppExchange Partner Data Scraper - Data Dictionary

This document details the schema of the final structured dataset output by the data pipeline, detailing which fields originate from the Salesforce API versus HTML parsing.

---

## Output Formats & Flattening Behavior

The pipeline exports two types of files to the `output/` directory:
1. **JSON (`partners.json`)**: Contains the fully nested, raw-typed structures for maximum data fidelity.
2. **CSV (`partners.csv`)**: A flattened tabular model optimized for spreadsheet analysis, database loads, and BI integration.

### CSV Flattening Rules:
- **Nested Dictionaries** (e.g., `contact`, `company`, `statistics`) are flattened into columns formatted as `parent_key_child_key` (e.g., `contact_email`, `company_logo`).
- **Lists** (e.g., `languages`, `resources`, `reviews`) are JSON-serialized as string values to ensure they occupy a single cell.
- **Flat Scalar Values** are written directly to their corresponding column headers.

---

## Dataset Schema

Below is the list of fields available in the final output and their source.

### 1. Primary API Fields
*These fields are extracted directly from the Salesforce AppExchange Apex API response by `PartnerTransformation`.*

| Field | CSV Column Name | Data Type | Description |
|---|---|---|---|
| `id` | `id` | String | Salesforce internal unique ID for the partner listing. |
| `name` | `name` | String | Legal name of the partner firm. |
| `headquarters` | `headquarters` | String | Primary headquarters city/region (API source). |
| `listing_url` | `listing_url` | String | AppExchange listing absolute URL. |
| `description` | `description` | String | General summary description of the partner business. |
| `projects` | `projects` | Integer | Total number of projects completed. |
| `credentials` | `credentials` | Integer | Number of Salesforce certifications/credentials held. |
| `reviews` | `reviews` | Integer | Total review count (API source). |
| `rating` | `rating` | Float | Average partner rating on AppExchange (API source). |
| `weighted_rating` | `weighted_rating` | Float | Internally calculated weighted rating. |
| `partner_score` | `partner_score` | Integer | Salesforce partner score. |
| `diverse_owned` | `diverse_owned` | Boolean | True if registered as a diverse-owned business. |
| `pledge_1_percent` | `pledge_1_percent` | Boolean | True if pledged to the "Pledge 1%" corporate initiative. |
| `expertise` | `expertise` | String | Semi-colon separated list of expertises (e.g. Sales Cloud; Service Cloud). |

---

### 2. Scraped HTML Fields
*These fields are extracted from the partner's listing HTML page by `HtmlTransformation`.*

#### Company Info (`company`)
| Field | CSV Column Name | Data Type | Description |
|---|---|---|---|
| `company_name` | `company_company_name` | String | Name parsed from the H1 listing header. |
| `logo` | `company_logo` | String | Logo image asset URL. |
| `banner` | `company_banner` | String | Listing banner image URL. |
| `tagline` | `company_tagline` | String | Extracted tagline (usually the first sentence of the overview). |

#### Statistics (`statistics`)
| Field | CSV Column Name | Data Type | Description |
|---|---|---|---|
| `rating` | `statistics_rating` | String | Average rating parsed from page body text. |
| `review_count` | `statistics_review_count` | String | Review count parsed from page body text. |
| `projects_completed` | `statistics_projects_completed`| String | Total projects completed text. |
| `certified_experts` | `statistics_certified_experts` | String | Certified experts count text. |
| `founded` | `statistics_founded` | String | Year of company foundation. |
| `employees` | `statistics_employees` | String | Employee size range. |

#### Contact Details (`contact`)
| Field | CSV Column Name | Data Type | Description |
|---|---|---|---|
| `website` | `contact_website` | String | Partner's corporate website URL. |
| `email` | `contact_email` | String | Public contact email address. |
| `phone` | `contact_phone` | String | Contact telephone number. |
| `headquarters` | `contact_headquarters` | String | Detailed street address of the headquarters (HTML source). |

#### Geographic Focus (`geographic`)
| Field | CSV Column Name | Data Type | Description |
|---|---|---|---|
| `countries` | `geographic_countries` | List[String] | Array of target countries serviced. |
| `states` | `geographic_states` | List[String] | Array of target states serviced (US/Canada). |

#### Lists & Nested structures
| Field | CSV Column Name | Data Type | Description |
|---|---|---|---|
| `languages` | `languages` | List[String] | List of corporate/business languages supported by the partner. |
| `resources` | `resources` | List[Dict] | Array of documents (guides, whitepapers, case studies) including keys: `title`, `url`. |
| `reviews` | `reviews` | List[Dict] | List of detailed reviews including keys: `reviewer`, `rating`, `date`, `review`. |
| `links` | `links` | Dict | Categorized list of hyperlinks extracted from the page. Keys: `internal`, `external`, `mailto`, `telephone`. |
| `about` | `about` | Dict | Raw key-value mappings of section attributes (e.g. "Services", "Industries"). |
| `description` | `description` | List[String] | Array of all description text paragraphs found on the page. |
| `highlight` | `highlight` | List[String] | Array of text bullet points listed as listing highlights. |
| `overview` | `overview` | Dict | General overview section contents containing keys: `title`, `description`. |
| `user_action` | `user_action` | Dict | Contains `learn_more_url` targeting registration/lead workflows. |
| `metadata` | `metadata` | Dict | Page SEO metadata containing `title`, `canonical` url, `description`, `keywords`, `robots` tags, and `og`/`twitter` parameters. |
