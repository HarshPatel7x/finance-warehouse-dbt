# Notes — Index

Navigation for the finance-warehouse-dbt build. Each step note is a beginner-language retro: what was
built, the concepts, the bugs, the decisions. New to a term? Start with the glossary.

## Concept reference
- **[glossary.md](./glossary.md)** — analytics-engineering concepts in dependency order: warehouse → ELT →
  dbt → source/seed → staging/marts (medallion) → materialization → star schema (fact/dimension) → grain →
  surrogate key → SCD Type 2 → snapshot → generic vs singular test → dbt-expectations → model contract →
  source freshness → exposure → lineage/DAG → CI gate.

## Build-step notes (in order)
| Step | Note | Covers |
|---|---|---|
| 1 | [step-01-repo-init.md](./step-01-repo-init.md) | Repo skeleton, **Python-3.12 pin (dbt #12098)**, dbt project/profile/packages, CI + pre-push, public repo |
| 2 | [step-02-generator-raw-load.md](./step-02-generator-raw-load.md) | Deterministic generator (40k tx / 24mo / 8 acct / 40 merchants, time-varying), `raw` load, dbt **source** + **freshness** |
| 3 | [step-03-staging.md](./step-03-staging.md) | Staging views (`stg_transactions/accounts/merchants`) + generic tests (unique, not_null, accepted_values, **relationships/FK**); CI → `dbt build` |
| 4 | [step-04-marts.md](./step-04-marts.md) | **Star schema** — `dim_account/merchant/date` + `fct_transactions` (grain test) + `mart_monthly_account_spend`; surrogate keys, FK + grain tests |
| 5 | [step-05-scd2-snapshot.md](./step-05-scd2-snapshot.md) | **SCD2** snapshot on merchants, **exercised** v1→v2 (6 closed-out versions, measured); invariant singular test; CI runs the full exercise |
| 6 | [step-06-data-quality.md](./step-06-data-quality.md) | Enforced **contract** + `dbt_expectations` + **singular** business-rule tests + YAML data contract; **demo: 12 generic green, 1 singular catches a bad row** |

*(steps 7–8 added as they ship)*

## Key findings (worth remembering)
- **A green generic test suite ≠ trustworthy data.** A structurally-perfect but business-invalid row
  (positive-amount payroll) passed all 12 generic/expectation tests on the fact; only a **singular** test
  caught it (Step 6, demonstrated).
- **SCD2 history is only as good as your change-detection grain** — the `check_cols` list. 6 mutated
  merchants → exactly 6 closed-out versions; widening `check_cols` to a noisy column would spuriously
  version everything (Step 5).
