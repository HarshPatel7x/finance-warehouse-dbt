# Step 6 — Data-quality gates: contracts, expectations, contracts-as-YAML (2026-06-05)

Turned "the data is probably fine" into "the build fails if it isn't." Added an enforced schema
**contract**, `dbt_expectations` value/distribution/row-count tests, business-rule **singular** tests, and a
legible YAML **data contract** — then *proved* a green generic suite can still hide a bad row.

> New term (contract, dbt_expectations, singular vs generic test, data contract)? See [`glossary.md`](./glossary.md).

---

## What we built

- **Enforced contract on `fct_transactions`** (`config: contract: {enforced: true}`): every output column
  declared with its `data_type` + a `not_null` constraint on the grain key. dbt now fails the build if the
  fact's shape drifts from the declaration.
- **`dbt_expectations` tests:** row-count baseline (`expect_table_row_count_to_be_between` 35k–45k),
  value range on `amount` (`expect_column_values_to_be_between` −4000..3000), and cardinality checks
  (`expect_column_distinct_count_to_equal` 8 accounts / 40 merchants).
- **Singular business-rule tests:** `assert_no_future_transactions`, `assert_inflow_categories_are_negative`.
- **A YAML data contract** on the BI mart (`meta.data_contract`: owner, freshness SLA, row-count baseline,
  consumer) — the human-readable contract the resume line promises.

Verified: full `dbt build` → **PASS=54, ERROR=0**.

---

## The headline finding (demonstrated, not claimed)

**A green generic test suite does not mean the data is trustworthy.** I injected one structurally-perfect
row — a *payroll* transaction with a **positive** amount (payroll should be money *in*), valid keys,
in-range date:

- **12 of 13** tests on `fct_transactions` — `unique`, `not_null`, all `relationships` (incl. the date FK),
  the value-range and row-count expectations — **PASSED**. The row is well-formed.
- The **one** test that caught it was the **singular** `assert_inflow_categories_are_negative`
  (*"Got 1 result, configured to fail if != 0"*).

The lesson for the README/interview: generic tests check *shape*; only singular tests encode *business
meaning*. A suite that's all generic can be 100% green over genuinely wrong data.

---

## Concepts taught (beginner language)

### 1. Model contract = an enforced schema promise
Declaring `contract: {enforced: true}` makes dbt compare the model's actual output columns and types to the
YAML and **fail the build** if they differ. That's a real "data contract": downstream BI can rely on
`fct_transactions` having exactly these columns and types, because a change that breaks the promise can't
merge.

### 2. dbt_expectations = richer assertions, still in-stack
Generic tests cover null/unique/membership/FK. `dbt_expectations` adds the Great-Expectations-style checks:
value ranges, row-count bounds, distinct-count, distribution — all running inside dbt with no extra
runtime. This is the free, in-stack reason we use it instead of standing up Great Expectations separately.

### 3. Singular vs generic — and why you need both
A **generic** test is a reusable YAML rule. A **singular** test is a one-off `SELECT` that returns the bad
rows. Business rules ("payroll is always an inflow", "no future-dated transactions") can't be expressed as
a generic rule, so they live as singular tests. The injected-row demo shows exactly why both matter.

### 4. A data contract is more than the schema
The full contract is four things: **schema** (the enforced column/type contract), **freshness SLA** (the
source freshness thresholds), **row-count baseline** (the expectation), and the **consumer list** (who
depends on it — wired as an exposure in Step 7). The `meta.data_contract` block writes all four down in one
legible place.

---

## Decisions locked

1. **Removed a vacuous test.** An earlier `assert_inflow_sign_matches_amount` could *never* fail — staging
   derives `is_inflow` from the sign, so the two are tautologically consistent. A test that can't fail is
   noise; replaced it with `assert_inflow_categories_are_negative`, which is genuinely violable (and powers
   the demo).
2. **Contract on the fact only.** `fct_transactions` is the BI-facing center of the star; contracting it is
   the highest-value schema promise without drowning every model in verbose type YAML.
3. **Expectation bands sized to the real data + margin** (amount −4000..3000 contains the measured
   −3197..2498) — tight enough to catch a 10× error, loose enough not to false-alarm.

---

## Gotchas encountered

- **Enforced contracts need EVERY column declared with `data_type`.** Miss one and the build errors. Pulled
  the exact types from `information_schema` first (varchar / integer / date / double / boolean) so the
  declaration matched on the first try.
- **The bad-row demo needed an *in-range* date.** A future date would also trip the `date_key` foreign-key
  test, muddying "generic green." Using an in-range payroll row keeps every generic test green so the
  singular test is unambiguously the one that catches it.

---

## What's next (Step 7 preview)

**Step 7 — exposure + docs + GitHub Pages.** Add an **exposure** naming the monthly-spend report as a real
downstream consumer (so lineage ends in a use), generate the `dbt docs` lineage graph, and deploy it to
GitHub Pages so the DAG is browsable at a public URL.
