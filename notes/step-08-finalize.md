# Step 8 — Finalize: measured metrics, honest limitations, live docs (2026-06-05)

Closed the build: filled the README metrics table with real `dbt build` numbers, verified the live Pages
lineage site loads, wrote the honest-limitations + résumé-claim sections, and confirmed a clean clone
reproduces green.

> New term? The full concept list is in [`glossary.md`](./glossary.md).

---

## What we built

- **README metrics table — measured, not TARGET.** 8 models · 44 tests (100% pass) · 40,000 fct rows ·
  SCD2 46 versions / 6 closed · ~3 s local build · 12/17 mart columns column-tested + the fact under an
  enforced contract.
- **Live docs verified.** Curled `https://harshpatel7x.github.io/finance-warehouse-dbt/` → HTTP 200,
  `<title>dbt Docs</title>`. Only after that did the word "deployed" go into the README.
- **Honest-limitations + résumé-claim sections** — static-seed freshness, single-writer DuckDB,
  MWAA/Snowflake as a documented-not-run promotion path, dbt_expectations-not-GE.

---

## Concepts taught (beginner language)

### 1. TARGET → MEASURED
Every metric carried a `TARGET` marker from Step 1 until a real run produced the number. That discipline
means the README never claims a figure that wasn't measured — the same rule the sibling repos use. A
recruiter can clone and reproduce every number.

### 2. "Deployed" is a verified word, not a hopeful one
The README says the lineage docs are *deployed* only because the live URL was fetched and returned the
page. Per the honesty rule, infrastructure claims are checked with a request, not asserted from a workflow
that "should" have published.

### 3. Honest limitations are a feature, not an apology
Naming what *isn't* built (live freshness, concurrent writers, cloud orchestration) is what makes the rest
credible. The cloud promotion path is framed exactly like the lakehouse repo frames AWS — local is the
faithful, $0, reproducible stand-in; promotion is a `profiles.yml` target + a scheduler, not a rewrite.

---

## Final shape of the warehouse

```
sources(3) → staging(3 views) → marts(5 tables: 3 dims + fct + monthly rollup)
                                   ├─ snapshot(1): SCD2 merchant history
                                   ├─ tests(45): generic + singular + dbt_expectations + 1 enforced contract
                                   └─ exposure(1): monthly_spend_report → reports/
CI: build+test gate on every PR · docs: lineage site on Pages on push to main · zero secrets
```

---

## Gotchas encountered

- **`dbt build` reports the snapshot as `no-op`** on a re-run when the source hasn't changed since the last
  snapshot — expected (nothing new to version), not an error.
- **Build time is tiny (~3 s)** because DuckDB is embedded and the corpus is 40k rows; the honest framing is
  "fast on this scale," not a throughput claim.

---

## What's next

Project complete. Follow-ups live in the parent career hub: reconcile the résumé's *dbt Warehouse* line to
this shipped scope (MWAA/GE → promotion path / dbt-expectations), and feature the repo on LinkedIn.
