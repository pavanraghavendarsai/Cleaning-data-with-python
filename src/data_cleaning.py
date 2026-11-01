import os
import pandas as pd

# =======================================================
# 0. LOAD RAW DATASETS (Never modify these directly)
# =======================================================
accounts = pd.read_csv("data/raw/accounts.csv")
invoices = pd.read_csv("data/raw/invoices.csv")
payments = pd.read_csv("data/raw/payments.csv")
plans = pd.read_csv("data/raw/plans.csv")
subscriptions = pd.read_csv("data/raw/subscriptions.csv")

datasets = {
    "accounts": accounts,
    "subscriptions": subscriptions,
    "invoices": invoices,
    "payments": payments,
    "plans": plans,
}

# =======================================================
# OVERVIEW: HIGH-LEVEL CHECK ACROSS ALL 5 TABLES
# =======================================================
for name, df in datasets.items():
    print(f"\n--- {name.upper()} ---")
    print("Shape (rows, columns):", df.shape)
    print("Exact duplicate rows:", df.duplicated().sum())
    print("Missing values per column:\n", df.isnull().sum())
    print("Unique values per column:\n", df.nunique())


# =======================================================
# TABLE 1: ACCOUNTS
# =======================================================

# --- STEP 1: INSPECT ---
# 1A. Check text categories for typos or extra spaces
# Finding: 'region' has " APAC" (leading space) and 479 missing (NaN) values.
print(accounts["region"].value_counts(dropna=False))
print(accounts["segment"].value_counts(dropna=False))
print(accounts["acquisition_channel"].value_counts(dropna=False))

# 1B. Check data types
# Finding: All columns are text (object/string). 'created_at' needs to be a date.
print(accounts.dtypes)

# 1C. Check primary key (account_id) for duplicates
# Finding: A000001 appears twice and both rows are 100% identical.
counts = accounts["account_id"].value_counts()
print("Duplicate account IDs:\n", counts[counts > 1])
print(accounts[accounts["account_id"] == "A000001"])

# 1D. Check foreign-key link to subscriptions
# Finding: All 2001 rows in subscriptions match a valid account_id.
print(subscriptions["account_id"].isin(accounts["account_id"]).value_counts())

# 1E. Check 'created_at' dates for formatting and realistic date ranges
# Finding: A000018 uses slashes ("2024/11/06") and A000030 is missing (NaN).
# Finding: All valid dates sit safely between 2023-01-01 and 2025-09-30.
properly_formatted_dates = pd.to_datetime(accounts["created_at"], errors="coerce")
missing_dates = properly_formatted_dates.isna()
print(
    "Rows that failed standard YYYY-MM-DD date check:\n",
    accounts.loc[missing_dates, ["account_id", "created_at"]],
)
print("Earliest date:", properly_formatted_dates.min())
print("Latest date:", properly_formatted_dates.max())

# --- STEP 2: PLAN ---
# 1. Make a copy called 'accounts_clean' so raw data stays untouched.
# 2. Drop the 1 exact duplicate row (A000001).
# 3. Strip extra spaces from 'region' (fixes " APAC") and fill NaN with "unknown".
# 4. Convert 'created_at' to datetime (fixing "2024/11/06" and leaving NaN as NaT).

# --- STEP 3: CLEAN ---
accounts_clean = accounts.copy()

# Remove any 100% identical duplicate rows
accounts_clean = accounts_clean.drop_duplicates()
print("New shape:", accounts_clean.shape)
print("Remaining duplicates:", accounts_clean.duplicated().sum())

# Strip extra spaces from 'region' and fill NaN with "unknown"
accounts_clean["region"] = accounts_clean["region"].str.strip()
accounts_clean = accounts_clean.fillna({"region": "unknown"})
print(accounts_clean["region"].value_counts())

# Convert 'created_at' to datetime (fixing "2024/11/06" and leaving NaN as NaT)
accounts_clean["created_at"] = pd.to_datetime(
    accounts_clean["created_at"], format="mixed", errors="coerce"
)

# --- STEP 4: VERIFY ---
assert accounts_clean["account_id"].nunique() == 2000
assert accounts_clean["region"].isnull().sum() == 0
assert accounts_clean["created_at"].isnull().sum() == 1


# =======================================================
# TABLE 2: PLANS
# =======================================================

# --- STEP 1: INSPECT ---
# Finding: Row 0 and Row 4 ("PLN_STARTER") are 100% identical duplicates.
# Finding: No missing values, text is clean, and numeric types (float64, int64) are correct.
print(plans)
print(plans.dtypes)
print(subscriptions["plan_id"].isin(plans["plan_id"]).value_counts())

# --- STEP 2: PLAN ---
# 1. Make a safe working copy called 'plans_clean' so raw data stays untouched.
# 2. Drop the 1 exact duplicate row ("PLN_STARTER").

# --- STEP 3: CLEAN ---
plans_clean = plans.copy()
plans_clean = plans_clean.drop_duplicates()

# --- STEP 4: VERIFY ---
assert plans_clean.shape == (4, 4)
assert plans_clean.duplicated().sum() == 0
assert plans_clean["plan_id"].nunique() == 4


# =======================================================
# TABLE 3: SUBSCRIPTIONS
# =======================================================

# --- STEP 1: INSPECT ---
print(subscriptions.info())
print(subscriptions.head(5))
print(subscriptions.duplicated().sum())
print(subscriptions[subscriptions["subscription_id"].duplicated(keep=False)])
print(subscriptions["status"].value_counts(dropna=False))
print(subscriptions[pd.to_datetime(subscriptions["started_at"], errors="coerce").isna()])
print(pd.to_datetime(subscriptions["ended_at"], errors="coerce").isna().value_counts())
print(subscriptions[["seats", "mrr"]].describe())

# --- STEP 2: PLAN ---
# 1. Create a safe copy (subscriptions_clean) and drop the 1 exact duplicate row (S000001).
# 2. Convert started_at to datetime using format='mixed' to rescue the slash-formatted date.
# 3. Convert ended_at to datetime using errors='coerce' (leaving active subscriptions as NaT).
# 4. Clean status text by stripping leading whitespace and converting to lowercase.

# --- STEP 3: CLEAN ---
subscriptions_clean = subscriptions.copy()
subscriptions_clean = subscriptions_clean.drop_duplicates()

subscriptions_clean["started_at"] = pd.to_datetime(
    subscriptions_clean["started_at"], format="mixed", errors="coerce"
)
subscriptions_clean["ended_at"] = pd.to_datetime(
    subscriptions_clean["ended_at"], errors="coerce"
)
subscriptions_clean["status"] = (
    subscriptions_clean["status"].str.strip().str.lower()
)

# --- STEP 4: VERIFY ---
assert subscriptions_clean["subscription_id"].duplicated().sum() == 0
assert subscriptions_clean["started_at"].isna().sum() == 1
assert subscriptions_clean["ended_at"].isna().sum() == 1590
assert (subscriptions_clean["status"] == " ACTIVE").sum() == 0
assert set(subscriptions_clean["status"]) == {"active", "cancelled"}
assert subscriptions_clean["account_id"].isin(accounts_clean["account_id"]).all()
assert subscriptions_clean["plan_id"].isin(plans_clean["plan_id"]).all()


# =======================================================
# TABLE 4: INVOICES
# =======================================================

# --- STEP 1: INSPECT ---
print(invoices.info())
print(invoices.head(10))
print(invoices[invoices.duplicated(keep=False)])
print(invoices["invoice_id"].duplicated().sum())
print(invoices["invoice_status"].value_counts(dropna=False))
print(invoices[pd.to_datetime(invoices["invoice_date"], errors="coerce").isna()])
print(pd.to_datetime(invoices["due_date"], errors="coerce").isna().value_counts())
print(invoices["amount_due"].describe())
print(invoices["subscription_id"].isin(subscriptions_clean["subscription_id"]).value_counts())

# --- STEP 2: PLAN ---
# 1. Create a safe copy (invoices_clean) and drop the 1 exact duplicate row (INV0000001).
# 2. Clean invoice_status by stripping extra spaces and converting to lowercase.
# 3. Convert invoice_date to datetime using format='mixed' to fix the slash-formatted date.
# 4. Convert due_date to datetime using errors='coerce'.

# --- STEP 3: CLEAN ---
invoices_clean = invoices.copy()
invoices_clean = invoices_clean.drop_duplicates()

invoices_clean["invoice_status"] = (
    invoices_clean["invoice_status"].str.strip().str.lower()
)
invoices_clean["invoice_date"] = pd.to_datetime(
    invoices_clean["invoice_date"], format="mixed", errors="coerce"
)
invoices_clean["due_date"] = pd.to_datetime(
    invoices_clean["due_date"], errors="coerce"
)

# --- STEP 4: VERIFY ---
assert invoices_clean["invoice_id"].duplicated().sum() == 0
assert invoices_clean["invoice_date"].isna().sum() == 1
assert invoices_clean["due_date"].isna().sum() == 0
assert (invoices_clean["invoice_status"] == " PAID ").sum() == 0
assert set(invoices_clean["invoice_status"]) == {"paid", "open", "void"}
assert invoices_clean["subscription_id"].isin(subscriptions_clean["subscription_id"]).all()


# =======================================================
# TABLE 5: PAYMENTS
# =======================================================

# --- STEP 1: INSPECT ---
print(payments.info())
print(payments.head(10))
print(payments[payments.duplicated(keep=False)])
print(payments["payment_id"].duplicated().sum())
print(payments["payment_status"].value_counts(dropna=False))
print(payments[pd.to_datetime(payments["attempted_at"], errors="coerce").isna()])
print(payments["amount"].describe())
print(payments["invoice_id"].isin(invoices_clean["invoice_id"]).value_counts())

# --- STEP 2: PLAN ---
# 1. Create a safe copy (payments_clean) and drop the 1 exact duplicate row (SPAY0000001).
# 2. Clean payment_status by stripping extra spaces and converting to lowercase (fixes " SUCCEEDED ").
# 3. Convert attempted_at to datetime using format='mixed' to rescue the slash-formatted date (2025/10/14) and keep the 1 missing value as NaT.

# --- STEP 3: CLEAN ---
payments_clean = payments.copy()
payments_clean = payments_clean.drop_duplicates()

payments_clean["payment_status"] = (
    payments_clean["payment_status"].str.strip().str.lower()
)
payments_clean["attempted_at"] = pd.to_datetime(
    payments_clean["attempted_at"], format="mixed", errors="coerce"
)

# --- STEP 4: VERIFY ---
assert payments_clean["payment_id"].duplicated().sum() == 0
assert payments_clean["attempted_at"].isna().sum() == 1
assert (payments_clean["payment_status"] == " SUCCEEDED ").sum() == 0
assert set(payments_clean["payment_status"]) == {"succeeded", "failed"}
assert payments_clean["invoice_id"].isin(invoices_clean["invoice_id"]).all()

print("All 5 tables (accounts, plans, subscriptions, invoices, payments) cleaned and verified!")


# =======================================================
# 6. EXPORT CLEANED DATA TO PROCESSED FOLDER
# =======================================================
processed_dir = "data/processed"
os.makedirs(processed_dir, exist_ok=True)

cleaned_datasets = {
    "accounts_clean.csv": accounts_clean,
    "plans_clean.csv": plans_clean,
    "subscriptions_clean.csv": subscriptions_clean,
    "invoices_clean.csv": invoices_clean,
    "payments_clean.csv": payments_clean,
}

for filename, df in cleaned_datasets.items():
    output_path = os.path.join(processed_dir, filename)
    df.to_csv(output_path, index=False)
    print(f"Saved: {output_path} ({df.shape[0]} rows, {df.shape[1]} cols)")
