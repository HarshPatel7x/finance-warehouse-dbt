# Step 4 — Marts: the star schema (2026-06-05)

The core modeling step. Turned the clean staging views into a **star schema** — dimensions + a fact +
a BI rollup — with surrogate keys and the tests that prove the star is internally consistent.

> New term (star schema, fact, dimension, grain, surrogate key)? See [`glossary.md`](./glossary.md).

---

## What we built

- **`dim_account`**, **`dim_merchant`**, **`dim_date`** — dimension tables (materialized as **tables**).
  `dim_date` is generated with `dbt_utils.date_spine` over the corpus range; each dim gets a **surrogate
  key**.
- **`fct_transactions`** — the fact. **Grain: one row per transaction.** Carries surrogate FKs to every
  dimension + the additive measure (`amount`).
- **`mart_monthly_account_spend`** — a BI rollup. Grain: one row per account per month
  (outflow / inflow / net / count).
- **`_marts__models.yml`** — `unique`+`not_null` on every key, **`relationships`** from the fact to all
  three dims, a **grain test** (unique `transaction_key`), and a multi-column uniqueness test on the
  monthly mart.

Verified: `dbt build --select staging marts` → **PASS=45, ERROR=0** (8 models + 37 tests).

---

## Concepts taught (beginner language)

### 1. Star schema: fact in the middle, dimensions around it
Drawn out, a fact table surrounded by its dimension tables looks like a star. The **fact**
(`fct_transactions`) holds the events and their numbers; the **dimensions** (`dim_account`,
`dim_merchant`, `dim_date`) hold the descriptive "who / what / when." "Total spend by merchant category
per month" becomes one clean fact-to-dim join instead of a tangle. It's the default warehouse shape
because it's fast to query and easy for an analyst to reason about.

### 2. Grain is the contract
The single most important sentence about a fact table is "one row represents ___." Here it's **one
transaction**. We *enforce* it with a `unique` test on `transaction_key`. If that test ever fails, a join
fanned out and every downstream number is silently doubled — grain bugs are the classic warehouse
disaster, so we test for them explicitly.

### 3. Surrogate keys
Instead of joining on the raw `account_id` string, each dimension gets a generated
`account_key = generate_surrogate_key(['account_id'])` (a hash). The fact carries the same hash. Surrogate
keys keep joins uniform, survive a source renaming its natural ids, and are what SCD2 history (Step 5)
hangs off of. dbt_utils builds them identically on both sides so the keys line up.

### 4. A generated date dimension
`dbt_utils.date_spine` emits one row per day across a range; we derive `year / quarter / month /
year_month / month_name / day_of_week / is_weekend` from it. A date dim lets you group by "weekday vs
weekend" or "Q3" without writing date math in every query — and `date_key` (a `yyyymmdd` integer) is a
compact FK on the fact.

### 5. Marts are **tables**, not views
Unlike staging, marts are materialized as real tables (`+materialized: table`). They're queried often, so
paying the compute once at build time (and reading fast after) beats re-running the query on every read.

---

## Decisions locked

1. **`dim_merchant` is the *current* merchant view here.** Its *history* is a separate concern handled by
   the SCD2 snapshot in Step 5 — keeping "what's true now" and "what was true then" as distinct objects.
2. **Integer `date_key` (`yyyymmdd`)**, not a raw date FK — compact, sorts naturally, the warehouse-classic
   choice.
3. **Tested the monthly mart's grain** with `dbt_utils.unique_combination_of_columns(account_key, month)` —
   a grain test on an aggregate, so a future GROUP BY mistake fails loudly.

---

## Gotchas encountered

- **DuckDB `extract(dow ...)` returns 0–6 (Sun=0).** Used that for the `is_weekend` flag (`in (0,6)`);
  worth knowing if you ever compare day-of-week numbers across engines (Postgres matches; some differ).
- **Surrogate-key formula must be byte-identical on both sides of a join.** The fact and each dim call the
  exact same `generate_surrogate_key([...])`, or the relationship test would (correctly) fail.

---

## Snippets worth remembering

### Surrogate key (same call on fact + dim)
```sql
{{ dbt_utils.generate_surrogate_key(['account_id']) }} as account_key
```

### Grain test = a uniqueness test on the grain column
```yaml
- name: transaction_key
  data_tests: [unique, not_null]   # one row per transaction, provably
```

---

## What's next (Step 5 preview)

**Step 5 — SCD2 history.** A `dbt snapshot` on the merchant dimension (check strategy on the changing
attributes), *exercised* by reloading scenario v2 (mutated merchants) and snapshotting again — so it
produces real closed-out version rows (`valid_from` / `valid_to`), not an empty history on static data.
