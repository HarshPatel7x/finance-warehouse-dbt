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

*(steps 5–8 added as they ship)*

## Key findings (worth remembering)
*(populated as the build surfaces them — candidates: "a green test suite doesn't mean trustworthy data";
"SCD2 history is only as good as your change-detection grain")*
