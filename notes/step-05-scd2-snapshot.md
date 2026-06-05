# Step 5 — SCD2 history (exercised, not theatre) (2026-06-05)

Added Slowly-Changing-Dimension Type 2 history on the merchant dimension — and actually **made it move**
by reloading a mutated scenario, so the snapshot produces real closed-out versions instead of an empty
history that only *looks* like SCD2.

> New term (SCD2, snapshot, valid_from/valid_to, check strategy)? See [`glossary.md`](./glossary.md).

---

## What we built

- **`snapshots/snap_merchant.sql`** — a `dbt snapshot`, `strategy='check'`, `check_cols=[merchant_name,
  category_primary, category_sub, city]`, `unique_key='merchant_id'`.
- **`tests/assert_one_current_merchant_version.sql`** — a **singular test** enforcing the SCD2 invariant:
  exactly one open (`dbt_valid_to is null`) version per merchant.
- **CI** now runs the full exercise: load v1 → baseline snapshot → reload v2 (mutated) → `dbt build`
  (the v2 snapshot closes/opens history + every test runs on real history).

### Measured (the honest number)
v1 baseline → 40 merchants, all current. Reload **v2** (6 merchants mutated) → snapshot again:

| | count |
|---|---|
| total versions | **46** |
| closed-out (`dbt_valid_to` set) | **6** |
| current (`dbt_valid_to is null`) | **40** |

Example history rows:
- `Blue Bottle` → `Blue Bottle Coffee` (rebrand)
- `Netflix`: `Subscription` → `Streaming` (reclassification)
- `Doordash`: `Restaurants` → `Grocery Delivery` (category pivot)

Full `dbt build` → **PASS=47, ERROR=0** (the SCD2 invariant test passes).

---

## Concepts taught (beginner language)

### 1. SCD Type 2 = keep the history, don't overwrite
When a merchant's category changes, Type 1 would just overwrite it and you'd lose the past. **Type 2**
instead closes the old row (`dbt_valid_to = now`) and opens a new version (`dbt_valid_from = now`,
`dbt_valid_to = null`). Now you can answer "what category was this in *March*?" — essential for honest
historical reporting (a transaction should be attributed to the category that was true *when it happened*).

### 2. `dbt snapshot` + the `check` strategy
A snapshot is dbt's built-in SCD2 machine. The **check** strategy says "watch these columns; if any
changed for a key since last run, version it." (The alternative, **timestamp** strategy, trusts an
`updated_at` column — we don't have a reliable one, so `check` is correct here.) dbt adds the bookkeeping
columns (`dbt_valid_from`, `dbt_valid_to`, `dbt_scd_id`) automatically.

### 3. Why it had to be **exercised**
A snapshot run once on static data produces history with **zero** closed rows — every `dbt_valid_to` is
null. That would *look* like SCD2 in the repo but prove nothing. So the generator ships a **v2 scenario**
that mutates a fixed set of merchants; running the snapshot across v1→v2 produces genuine closed-out
versions. The measured "6 closed" is a real number, reproduced in CI — not a claim.

### 4. The invariant test
SCD2 history is corrupt the moment a key has two "current" rows. The singular test
`assert_one_current_merchant_version` returns any merchant with >1 open version; green means the history is
internally consistent. Generic tests can't express this — it needs a custom `SELECT`.

---

## Decision / finding worth remembering

**The headline:** SCD2 history is only as good as your **change-detection grain** — the `check_cols` list.
I mutated exactly 6 merchants across 4 watched attributes and got exactly 6 closed versions: no missed
changes, no spurious ones. Widen `check_cols` to include a noisy column (say a load timestamp) and every
run would spuriously version every row; narrow it and you'd silently miss real changes. Choosing *which
columns count as a change* is the actual modeling judgment — `dbt snapshot` just executes it.

---

## Gotchas encountered

- **Snapshot the SOURCE, not a model.** `snap_merchant` reads `source('raw','merchants')` directly. Pointing
  a snapshot at a `ref()` model drags model-build ordering into snapshot timing; sourcing keeps it simple
  and is the conventional pattern.
- **DuckDB is single-writer.** The generator must fully close its connection before `dbt snapshot` opens
  the file, or the second writer is locked out. The CI steps are ordered to guarantee that.

---

## What's next (Step 6 preview)

**Step 6 — data-quality gates.** Enforced model **contracts** (column types/constraints) + `dbt_expectations`
value/distribution/row-count tests + more **singular** tests (no future-dated transactions, debit/credit
sign rules) + a YAML **data contract** (schema + freshness SLA + row-count baseline + consumer list) — and
a demonstration that a green *generic* suite can still hide a known-bad row that only a singular test catches.
