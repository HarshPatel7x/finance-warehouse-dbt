"""Generate the synthetic finance corpus and load it into the DuckDB `raw` schema.

This EXPANDS the shared seed=42 finance corpus (originally 693 rows / one account,
from the finance-pipeline repo) to a size that can honestly demonstrate analytics
engineering: ~40k transactions over 24 months across multiple accounts, plus a
merchant dimension whose attributes CHANGE between scenario v1 and v2 — which is
what makes the SCD2 snapshot (Step 5) capture real history instead of theatre.

Deterministic: same seed -> byte-identical tables, so CI and a recruiter's clone
reproduce the exact warehouse.

Tables written (schema `raw`):
  raw.accounts      one row per account
  raw.merchants     one row per merchant (THIS is the SCD2 dimension; v2 mutates it)
  raw.transactions  the fact: one row per transaction, stamped with `_loaded_at`

Usage:
  python scripts/generate_and_load.py                # scenario v1 (default)
  python scripts/generate_and_load.py --scenario v2  # mutate a fixed set of merchants
"""
from __future__ import annotations

import argparse
import random
from datetime import date, datetime, timedelta, timezone

import duckdb

SEED = 42
N_TRANSACTIONS = 40_000
START = date(2023, 6, 1)
END = date(2025, 5, 31)
DB_PATH = "finance_warehouse.duckdb"

# (account_id, name, type, open_date)
ACCOUNTS = [
    ("acc_001", "Everyday Checking", "checking", date(2021, 1, 15)),
    ("acc_002", "High-Yield Savings", "savings", date(2021, 1, 15)),
    ("acc_003", "Rewards Credit Card", "credit", date(2021, 3, 2)),
    ("acc_004", "Travel Credit Card", "credit", date(2022, 6, 10)),
    ("acc_005", "Joint Checking", "checking", date(2022, 9, 1)),
    ("acc_006", "Brokerage Cash", "investment", date(2023, 2, 20)),
    ("acc_007", "Business Checking", "checking", date(2023, 5, 5)),
    ("acc_008", "Emergency Savings", "savings", date(2023, 8, 12)),
]

# (merchant_id, name, category_primary, category_sub, city) — the v1 baseline.
# Spend ranges per sub-category drive the transaction amounts below.
MERCHANTS = [
    ("mch_01", "Costco", "Shops", "Supermarkets and Groceries", "Seattle"),
    ("mch_02", "Whole Foods", "Shops", "Supermarkets and Groceries", "Austin"),
    ("mch_03", "Trader Joe's", "Shops", "Supermarkets and Groceries", "Pasadena"),
    ("mch_04", "Starbucks", "Food and Drink", "Coffee Shop", "Seattle"),
    ("mch_05", "Blue Bottle", "Food and Drink", "Coffee Shop", "Oakland"),
    ("mch_06", "Chipotle", "Food and Drink", "Restaurants", "Denver"),
    ("mch_07", "Olive Garden", "Food and Drink", "Restaurants", "Orlando"),
    ("mch_08", "Shake Shack", "Food and Drink", "Restaurants", "New York"),
    ("mch_09", "Delta Air Lines", "Travel", "Airlines and Aviation", "Atlanta"),
    ("mch_10", "United Airlines", "Travel", "Airlines and Aviation", "Chicago"),
    ("mch_11", "Uber", "Travel", "Ride Share", "San Francisco"),
    ("mch_12", "Lyft", "Travel", "Ride Share", "San Francisco"),
    ("mch_13", "Marriott", "Travel", "Lodging", "Bethesda"),
    ("mch_14", "Amazon", "Shops", "Digital Purchase", "Seattle"),
    ("mch_15", "Best Buy", "Shops", "Electronics", "Richfield"),
    ("mch_16", "Apple Store", "Shops", "Electronics", "Cupertino"),
    ("mch_17", "Nike", "Shops", "Clothing and Accessories", "Beaverton"),
    ("mch_18", "Zara", "Shops", "Clothing and Accessories", "New York"),
    ("mch_19", "Shell", "Travel", "Gas Stations", "Houston"),
    ("mch_20", "Chevron", "Travel", "Gas Stations", "San Ramon"),
    ("mch_21", "Netflix", "Service", "Subscription", "Los Gatos"),
    ("mch_22", "Spotify", "Service", "Subscription", "New York"),
    ("mch_23", "Comcast Xfinity", "Service", "Utilities", "Philadelphia"),
    ("mch_24", "PG&E", "Service", "Utilities", "Oakland"),
    ("mch_25", "Equinox", "Recreation", "Gyms and Fitness Centers", "New York"),
    ("mch_26", "Planet Fitness", "Recreation", "Gyms and Fitness Centers", "Hampton"),
    ("mch_27", "CVS Pharmacy", "Shops", "Pharmacies", "Woonsocket"),
    ("mch_28", "Walgreens", "Shops", "Pharmacies", "Deerfield"),
    ("mch_29", "Home Depot", "Shops", "Hardware Store", "Atlanta"),
    ("mch_30", "IKEA", "Shops", "Furniture and Home", "Conshohocken"),
    ("mch_31", "Acme Payroll", "Transfer", "Payroll", "New York"),
    ("mch_32", "Vanguard", "Transfer", "Investment", "Malvern"),
    ("mch_33", "Venmo", "Transfer", "Third Party", "New York"),
    ("mch_34", "Bank of America", "Payment", "Credit Card", "Charlotte"),
    ("mch_35", "Geico", "Service", "Insurance", "Chevy Chase"),
    ("mch_36", "AT&T", "Service", "Telecom", "Dallas"),
    ("mch_37", "Doordash", "Food and Drink", "Restaurants", "San Francisco"),
    ("mch_38", "Target", "Shops", "Department Stores", "Minneapolis"),
    ("mch_39", "Walmart", "Shops", "Supermarkets and Groceries", "Bentonville"),
    ("mch_40", "Sweetgreen", "Food and Drink", "Restaurants", "Los Angeles"),
]

# sub-category -> (min, max) absolute spend; sign applied below.
SPEND_RANGES = {
    "Supermarkets and Groceries": (15, 240),
    "Coffee Shop": (4, 18),
    "Restaurants": (12, 95),
    "Airlines and Aviation": (120, 780),
    "Ride Share": (8, 55),
    "Lodging": (140, 520),
    "Digital Purchase": (6, 160),
    "Electronics": (40, 1300),
    "Clothing and Accessories": (20, 280),
    "Gas Stations": (25, 85),
    "Subscription": (8, 23),
    "Utilities": (45, 220),
    "Gyms and Fitness Centers": (15, 240),
    "Pharmacies": (6, 90),
    "Hardware Store": (12, 460),
    "Furniture and Home": (30, 900),
    "Payroll": (1800, 3200),          # inflow (sign flipped negative)
    "Investment": (200, 2500),
    "Third Party": (10, 300),
    "Credit Card": (50, 1400),        # card payment (inflow to the card)
    "Insurance": (60, 190),
    "Telecom": (35, 120),
    "Department Stores": (10, 220),
}
INFLOW_SUBS = {"Payroll", "Credit Card"}  # negative amounts = money in

# v2 mutations: a FIXED set of merchant changes, so SCD2 history is deterministic.
#   - rebrands (name change) and reclassifications (category change)
V2_MUTATIONS = {
    "mch_05": {"merchant_name": "Blue Bottle Coffee"},                 # rebrand
    "mch_21": {"category_sub": "Streaming"},                           # reclassified
    "mch_37": {"category_primary": "Shops", "category_sub": "Grocery Delivery"},  # pivot
    "mch_33": {"merchant_name": "Venmo (PayPal)"},                     # rebrand
    "mch_25": {"city": "Los Angeles"},                                 # relocation
    "mch_15": {"category_sub": "Computers and Electronics"},           # retitle
}


def merchants_for(scenario: str):
    rows = []
    for mid, name, cat_p, cat_s, city in MERCHANTS:
        rec = {"merchant_id": mid, "merchant_name": name,
               "category_primary": cat_p, "category_sub": cat_s, "city": city}
        if scenario == "v2" and mid in V2_MUTATIONS:
            rec.update(V2_MUTATIONS[mid])
        rows.append(rec)
    return rows


def generate_transactions(rng: random.Random):
    span = (END - START).days
    sub_by_merchant = {m[0]: m[3] for m in MERCHANTS}
    name_by_merchant = {m[0]: m[1] for m in MERCHANTS}
    account_ids = [a[0] for a in ACCOUNTS]
    merchant_ids = [m[0] for m in MERCHANTS]
    rows = []
    for i in range(1, N_TRANSACTIONS + 1):
        mid = rng.choice(merchant_ids)
        sub = sub_by_merchant[mid]
        lo, hi = SPEND_RANGES[sub]
        amt = round(rng.uniform(lo, hi), 2)
        if sub in INFLOW_SUBS:
            amt = -amt
        d = START + timedelta(days=rng.randint(0, span))
        rows.append({
            "transaction_id": f"tx_{i:06d}",
            "date": d,
            "account_id": rng.choice(account_ids),
            "merchant_id": mid,
            "name": name_by_merchant[mid],
            "amount": amt,
            "pending": rng.random() < 0.02,
        })
    return rows


def load(scenario: str):
    rng = random.Random(SEED)
    accounts = [{"account_id": a, "account_name": n, "account_type": t, "open_date": o}
                for (a, n, t, o) in ACCOUNTS]
    merchants = merchants_for(scenario)
    transactions = generate_transactions(rng)
    loaded_at = datetime.now(timezone.utc)

    con = duckdb.connect(DB_PATH)
    con.execute("CREATE SCHEMA IF NOT EXISTS raw;")

    con.execute("DROP TABLE IF EXISTS raw.accounts;")
    con.execute("""CREATE TABLE raw.accounts (
        account_id VARCHAR, account_name VARCHAR, account_type VARCHAR, open_date DATE);""")
    con.executemany("INSERT INTO raw.accounts VALUES (?,?,?,?)",
                    [(a["account_id"], a["account_name"], a["account_type"], a["open_date"])
                     for a in accounts])

    con.execute("DROP TABLE IF EXISTS raw.merchants;")
    con.execute("""CREATE TABLE raw.merchants (
        merchant_id VARCHAR, merchant_name VARCHAR, category_primary VARCHAR,
        category_sub VARCHAR, city VARCHAR, _loaded_at TIMESTAMPTZ);""")
    con.executemany("INSERT INTO raw.merchants VALUES (?,?,?,?,?,?)",
                    [(m["merchant_id"], m["merchant_name"], m["category_primary"],
                      m["category_sub"], m["city"], loaded_at) for m in merchants])

    con.execute("DROP TABLE IF EXISTS raw.transactions;")
    con.execute("""CREATE TABLE raw.transactions (
        transaction_id VARCHAR, date DATE, account_id VARCHAR, merchant_id VARCHAR,
        name VARCHAR, amount DOUBLE, pending BOOLEAN, _loaded_at TIMESTAMPTZ);""")
    con.executemany("INSERT INTO raw.transactions VALUES (?,?,?,?,?,?,?,?)",
                    [(t["transaction_id"], t["date"], t["account_id"], t["merchant_id"],
                      t["name"], t["amount"], t["pending"], loaded_at) for t in transactions])

    n_tx = con.execute("SELECT count(*) FROM raw.transactions").fetchone()[0]
    n_ac = con.execute("SELECT count(*) FROM raw.accounts").fetchone()[0]
    n_mc = con.execute("SELECT count(*) FROM raw.merchants").fetchone()[0]
    con.close()
    print(f"[{scenario}] loaded raw.transactions={n_tx}  raw.accounts={n_ac}  "
          f"raw.merchants={n_mc}  _loaded_at={loaded_at.isoformat()}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", choices=["v1", "v2"], default="v1",
                    help="v1 = baseline; v2 = mutate a fixed set of merchants (for SCD2).")
    args = ap.parse_args()
    load(args.scenario)
