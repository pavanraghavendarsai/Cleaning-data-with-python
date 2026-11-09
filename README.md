# SaaS Database — Data Quality Audit & Cleaning Pipeline

## 1. Executive Summary
This project executes a systematic **Inspect → Plan → Clean → Verify** data engineering workflow across five core relational tables of a B2B SaaS billing database (`accounts`, `plans`, `subscriptions`, `invoices`, `payments`). 

Raw CSV datasets from `data/raw/` were audited for primary-key uniqueness, referential integrity, categorical consistency, temporal formatting, and missingness. All transformations were validated using programmatic `assert` checks before exporting clean datasets to `data/processed/`.

**Data Source:** [Analytics Engineering — SaaS Subscriptions & Customer Churn Dataset (v1.0.0 Data-Cleaning Challenge)](https://www.analyticsengineering.com/datasets/saas-subscriptions) (Synthetic Educational Data, coverage: 2023-01-01 to 2025-12-31).


## 2. Relational Schema & Referential Integrity
The database follows a strict hierarchical dependency order:
* **Parent Tables:** `accounts` (`account_id`), `plans` (`plan_id`)
* **Level 1 Child:** `subscriptions` (`subscription_id`) → references `accounts.account_id` and `plans.plan_id`
* **Level 2 Child:** `invoices` (`invoice_id`) → references `subscriptions.subscription_id`
* **Level 3 Child:** `payments` (`payment_id`) → references `invoices.invoice_id`

**Foreign-Key Validation Result:** 100% of foreign keys across all child tables matched valid primary keys in their respective cleaned parent tables (zero orphan records detected).

## 3. Summary of Anomalies & Resolutions Across All Tables

| Table | Raw Rows | Clean Rows | Duplicate PK Removed | Categorical String Fix | Date Format Rescued | Missing Values (`NaN` / `NaT`) Handled |
| :--- | :---: | :---: | :--- | :--- | :--- | :--- |
| **accounts** | 2,001 | 2,000 | `A000001` | `region`: `" APAC"` → `"APAC"` | `created_at`: `2024/11/06` (`A000018`) | 479 missing `region` filled with `"unknown"`; 1 missing `created_at` (`A000030`) kept as `NaT` |
| **plans** | 5 | 4 | `PLN_STARTER` | None required | No date columns | 0 missing values |
| **subscriptions** | 2,001 | 2,000 | `S000001` | `status`: `" ACTIVE"` → `"active"` | `started_at`: `2024/10/01` (`S000018`) | 1 missing `started_at` (`S000030`) kept as `NaT`; 1,590 missing `ended_at` kept as `NaT` (active) |
| **invoices** | 2,001 | 2,000 | `INV0000001` | `invoice_status`: `" PAID "` → `"paid"` | `invoice_date`: `2025/11/11` (`INV0000018`) | 1 missing `invoice_date` (`INV0000030`) kept as `NaT`; 0 missing `due_date` |
| **payments** | 2,001 | 2,000 | `SPAY0000001` | `payment_status`: `" SUCCEEDED "` → `"succeeded"` | `attempted_at`: `2025/10/14` (`SPAY0000018`) | 1 missing `attempted_at` (`SPAY0000030`) kept as `NaT` |

## 4. Detailed Engineering Decisions

### 4.1 Primary Key Deduplication
Every table contained exactly one 100% identical duplicate row appended at the end of the file (index `2000` duplicating index `0`). Exact duplicates were removed via `.drop_duplicates()`, restoring 100% primary-key uniqueness across all five tables.

### 4.2 Categorical Normalization
Leading and trailing whitespace combined with inconsistent casing (such as `" APAC"`, `" ACTIVE"`, `" PAID "`, and `" SUCCEEDED "`) caused pandas to treat identical categories as distinct values. String columns were normalized using `.str.strip()` and `.str.lower()` (with uppercase preserved for region codes).

### 4.3 Temporal Parsing & Data Rescue
All date columns (`created_at`, `started_at`, `ended_at`, `invoice_date`, `due_date`, `attempted_at`) were initially loaded as `object` strings. Standard `YYYY-MM-DD` parsing flagged one row at index `17` in each transactional table due to slash separators (`YYYY/MM/DD`). Passing `format="mixed"` and `errors="coerce"` to `pd.to_datetime()` rescued all slash-formatted dates without coercing valid records to `NaT`.

### 4.4 Missing Value (`NaN`) Policy
* **Categorical Imputation (`accounts.region`):** 479 missing region values (~24% of accounts) were explicitly filled with `"unknown"` to prevent silent row drops during downstream `GROUP BY` aggregations.
* **Domain-Valid Nulls (`subscriptions.ended_at`):** 1,590 missing `ended_at` timestamps correspond directly to currently active subscriptions and were preserved as `NaT`.
* **True Missing Timestamps:** Exactly 1 record per transactional table (index `29`: `A000030`, `S000030`, `INV0000030`, `SPAY0000030`) lacked a creation/attempt date in the raw source. These were preserved as `NaT` rather than fabricated to maintain audit accuracy.

## 5. Automated Verification (`assert` Checks)
Before exporting to `data/processed/`, automated assertions verified:
1. Zero duplicate primary keys across all 5 tables.
2. Exact expected `NaT` counts in all `datetime64[ns]` columns.
3. Strict set-membership checks on categorical columns:
   * `subscriptions_clean["status"]` in `{"active", "cancelled"}`
   * `invoices_clean["invoice_status"]` in `{"paid", "open", "void"}`
   * `payments_clean["payment_status"]` in `{"succeeded", "failed"}`
4. 100% referential integrity across all parent-child foreign keys using `.isin().all()`.

## 6. How to Run Locally

1. Clone the repository and move into the project folder:

   ```bash
   git clone https://github.com/pavanraghavendarsai/Cleaning-data-with-python.git
   cd Cleaning-data-with-python
   ```

2. (Optional) Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Windows: .venv\Scripts\activate
   ```

3. Install dependencies (requires pandas 2.0 or later):

   ```bash
   pip install -r requirements.txt
   ```

4. Run the cleaning script from the project root folder:

   ```bash
   python src/data_cleaning.py
   ```

5. The cleaned files are saved to `data/processed/`.
