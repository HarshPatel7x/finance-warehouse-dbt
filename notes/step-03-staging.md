# Step 3 — Staging layer + generic tests (2026-06-05)

Built the first dbt models: one cleaned view per source table, plus the generic tests that make the
foundation trustworthy before any marts get stacked on top.

> New term (staging, view, generic test, relationships)? See [`glossary.md`](./glossary.md).

---

## What we built

- **`stg_transactions`**, **`stg_accounts`**, **`stg_merchants`** — views (`+materialized: view`) that
  rename, type, and lightly derive (`is_inflow`, `abs_amount`) — **no business logic**.
- **`_finance__models.yml`** — generic tests on each: `unique` + `not_null` on every key,
  `relationships` (foreign-key) from transactions → accounts and → merchants, `accepted_values` on
  `account_type` and `category_primary`.
- **CI upgraded** from `dbt parse` to **`dbt build`** — now every PR builds the models *and* runs the tests.

Verified locally: `dbt build --select staging` → **PASS=17, ERROR=0** (3 views + 14 data tests).

---

## Concepts taught (beginner language)

### 1. The staging layer: one clean view per source
Staging is a thin, boring layer with one model per raw table. Its only jobs: rename columns to a
consistent style, fix types, and maybe add a trivial derived column. **No joins, no aggregations, no
business rules.** That discipline means every downstream model starts from the same clean base, and a bug
is easy to trace because each transform does exactly one thing.

### 2. Why staging models are **views**
A view is just a saved query — it stores no data, it re-runs against the source each time. Staging is
cheap, always reflects the latest raw data, and costs no storage. Marts (the expensive, queried layer) are
**tables**. Picking view-vs-table per layer is a real modeling decision (`dbt_project.yml` sets it).

### 3. Generic tests = reusable data assertions in YAML
Four built-ins do most of the work:
- **`unique`** — no duplicate keys.
- **`not_null`** — required columns are populated.
- **`accepted_values`** — a column only holds values from an allowed set (catches a typo'd category).
- **`relationships`** — every `merchant_id` in transactions actually exists in merchants (a **foreign-key /
  referential-integrity** check). This is the test that catches orphaned facts.

Each is one line of YAML and runs on every `dbt build`. Green tests = the data matches the shape you
promised.

### 4. `ref()` builds the dependency graph
`stg_transactions` reads `{{ source('raw','transactions') }}`; the `relationships` test references
`ref('stg_accounts')`. Every `ref()`/`source()` is an edge in dbt's lineage DAG — which is how dbt knows
to build accounts before the test that depends on it, and what to show in the docs graph later.

---

## Decisions locked

1. **Derive `is_inflow` / `abs_amount` in staging, not marts.** They're pure row-level reshapes (no
   business logic), so staging is their right home — marts can assume a clean, typed base.
2. **FK integrity tested at staging.** Relationship tests live here so a broken reference fails *before*
   marts are built on bad joins.

---

## Gotchas encountered

- **`MissingArgumentsPropertyInGenericTestDeprecation` warning.** dbt 1.11 is previewing a future syntax
  where generic-test args nest under an `arguments:` key. The classic inline form
  (`accepted_values: {values: [...]}`) still works and is what every dbt repo + tutorial uses, so we kept
  it for readability; it's a warning, not an error. Worth migrating only if we ever pin dbt 2.0.

---

## Snippets worth remembering

### A foreign-key (referential-integrity) test
```yaml
- name: merchant_id
  data_tests:
    - not_null
    - relationships:
        to: ref('stg_merchants')
        field: merchant_id
```

### Build + test just one layer
```bash
dbt build --select staging --profiles-dir .
```

---

## What's next (Step 4 preview)

**Step 4 — marts (star schema).** Build `dim_account`, `dim_merchant`, `dim_date`, and the
`fct_transactions` fact (grain = one transaction, surrogate keys via dbt_utils), plus
`mart_monthly_account_spend`. Add relationship + grain tests so the star is provably consistent.
