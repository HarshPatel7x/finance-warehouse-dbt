# Step 2 — Synthetic generator + raw load (2026-06-05)

Built the data the whole warehouse stands on: a deterministic generator that expands the shared finance
corpus and loads it into DuckDB's `raw` schema, declared to dbt as a **source** with a real freshness check.

> New term (source, freshness, grain, ELT)? See [`glossary.md`](./glossary.md).

---

## What we built

- **`scripts/generate_and_load.py`** — seed=42, **40,000 transactions** over **24 months** (2023-06 →
  2025-05), **8 accounts**, **40 merchants**. Writes three `raw` tables: `raw.accounts`, `raw.merchants`,
  `raw.transactions`. Each fact + merchant row is stamped with a real `_loaded_at` UTC timestamp.
- **`models/staging/_finance__sources.yml`** — declares the `raw` source + a **freshness** check on
  `_loaded_at` (warn > 24h, error > 72h).
- **CI** now loads the corpus and runs `dbt source freshness` on every PR.

Verified: `raw.transactions=40000`, 8 distinct accounts, 40 merchants, 2,044 inflow rows; re-running gives
an identical amount-sum (deterministic). `dbt source freshness` → **PASS** on both sources.

---

## Concepts taught (beginner language)

### 1. Why EXPAND the corpus (693 → 40k, 1 → 8 accounts, time-varying merchants)
The original shared corpus is 693 rows on a single account. You **cannot** honestly demonstrate SCD2
(history of *changes*), incremental models (new rows over time), or freshness on data that never changes
and has one of everything. So the generator grows it on purpose — and builds a **merchant dimension whose
attributes change** between scenario v1 and v2 (rebrands, reclassifications). That change is what Step 5's
snapshot will capture. Growing synthetic data to fit the skill you're proving is itself a DE skill.

### 2. Deterministic generation (seed=42)
One `random.Random(42)` drives every choice, so the tables are byte-stable: CI and a recruiter's clone
rebuild the *exact* same 40k rows. Reproducibility is the point — a portfolio repo that generates
different data each run can't have trustworthy metrics.

### 3. `raw` schema = the landing zone (the "E + L" of ELT)
The generator does **Extract + Load** only — it lands raw rows and does **no** business logic. All cleaning
and modeling happens later, in dbt, in SQL (the "T"). Keeping raw untouched means you can always rebuild
the warehouse from a known starting point.

### 4. A dbt **source** vs a seed
The raw tables already live in DuckDB (the loader put them there), so dbt reads them as a **source**
(`source('raw','transactions')`) rather than a **seed** (a CSV dbt loads itself). Sources are the right
model for "data some upstream process loaded" — and only sources support **freshness**.

### 5. Honest **freshness**
Freshness = "how stale is this source?" dbt compares `now()` to the newest `_loaded_at`. On a one-shot
static seed the loader just ran, so it's **trivially fresh** — and the YAML says so in a comment. The
honest value: the check is *real*. If a scheduled loader ever fell more than 24h behind, this exact check
would warn; past 72h it would fail CI. We did **not** fake staleness or claim live monitoring.

---

## Decisions locked

1. **Amount sign convention:** negative = money **in** (payroll, card payment), positive = money out —
   matching the original finance-pipeline corpus, so the portfolio stays consistent.
2. **Merchant is the SCD2 dimension** (not account). Merchants rebrand/reclassify in the real world; the v2
   mutation set is fixed and deterministic so the resulting history is reproducible.
3. **Freshness on `_loaded_at`, not transaction `date`.** Freshness is about the *pipeline* (load lag), not
   business recency — conflating them would be dishonest.

---

## Gotchas encountered

- **`accounts` has no `_loaded_at`.** Only `transactions` + `merchants` carry it, so only those two declare
  freshness. Adding a meaningless timestamp to a tiny static lookup just to claim "freshness everywhere"
  would be theatre — left it off.
- **Write with the `duckdb` lib, read with dbt — sequentially.** The generator opens the `.duckdb` file,
  writes, and **closes** before dbt touches it. DuckDB is single-writer; overlapping connections would lock.

---

## Snippets worth remembering

### Source with a real freshness SLA
```yaml
- name: transactions
  loaded_at_field: _loaded_at
  freshness:
    warn_after:  {count: 24, period: hour}
    error_after: {count: 72, period: hour}
```

### Two scenarios from one generator (sets up SCD2)
```bash
python scripts/generate_and_load.py              # v1 baseline
python scripts/generate_and_load.py --scenario v2  # mutate fixed merchants (Step 5)
```

---

## What's next (Step 3 preview)

**Step 3 — staging layer.** One cleaned view per source (`stg_transactions`, `stg_accounts`,
`stg_merchants`): rename, type, split the category, no business logic — plus generic tests (`not_null`,
`unique`, `accepted_values`, `relationships`) so the foundation is trustworthy before marts are built.
