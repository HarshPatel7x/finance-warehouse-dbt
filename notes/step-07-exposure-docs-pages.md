# Step 7 — Exposure + lineage docs on GitHub Pages (2026-06-05)

Made the lineage end in a real **use**, then published the whole dependency graph as a browsable site.

> New term (exposure, lineage/DAG, dbt docs)? See [`glossary.md`](./glossary.md).

---

## What we built

- **`scripts/report.py`** — a real downstream **consumer**: reads `mart_monthly_account_spend` + dims and
  writes `reports/monthly_spend_summary.md` (spend by account, top categories) with real numbers
  (8 accounts, 24 months).
- **`models/exposures/_exposures.yml`** — a dbt **exposure** `monthly_spend_report` that names that report
  as a consumer and `depends_on` the mart + dims. Now the lineage graph terminates in a use, not a stub.
- **`.github/workflows/docs.yml`** — builds the warehouse on a clean runner, runs `dbt docs generate
  --static` (one self-contained HTML), and deploys it to **GitHub Pages** on every push to main.
- **Enabled Pages** (Actions source) → site at `https://harshpatel7x.github.io/finance-warehouse-dbt/`.

Verified locally: report writes 8 accounts × 24 months; `dbt docs generate --static` → a 2.9 MB
`static_index.html`; the exposure parses (`dbt ls --select exposure:*`).

---

## Concepts taught (beginner language)

### 1. An exposure = "who consumes this data"
dbt knows your models depend on each other, but it doesn't know a *dashboard* or a *report* downstream
depends on a mart — unless you tell it with an **exposure**. The exposure names the consumer, links it to
the models it reads, and shows up at the end of the lineage graph. The payoff: you can ask "if I change
`mart_monthly_account_spend`, what breaks?" and the answer includes the report, not just other models.

### 2. Lineage ending in a real use, not a stub
The adversarial-review note here was: an exposure pointing at an imaginary dashboard is decoration. So the
consumer is **real** — `scripts/report.py` actually queries the mart and produces a committed markdown
report. The exposure's `url` points at that file. If the mart's grain or columns changed, the report
script would break — which is the whole point of declaring the dependency.

### 3. `dbt docs` + the `--static` flag
`dbt docs generate` builds a catalog (`catalog.json`) + the manifest and renders an interactive site: every
model, its columns, its tests, its SQL, and the clickable lineage DAG. The **`--static`** flag inlines it
all into a single self-contained `static_index.html` — perfect for hosting on Pages with no separate JSON
files to serve.

### 4. GitHub Pages from Actions (zero secrets)
The deploy uses the official `upload-pages-artifact` + `deploy-pages` actions with the default
`GITHUB_TOKEN` — no PAT, no secret. Pages is set to "GitHub Actions" as its build source. Because the repo
is **public**, Pages is free; that's why this project was public from Step 1.

---

## Decisions locked

1. **Commit the generated report.** `reports/monthly_spend_summary.md` is deterministic (seed=42) and is
   the artifact the exposure URL points at, so it's committed and viewable on GitHub — not gitignored.
2. **`--static` single file**, not the multi-file docs site — simplest thing to put on Pages, no asset-path
   juggling.
3. **Docs deploy on push to main only.** PRs run the build/test CI; the public site only updates once a step
   actually lands on main.

---

## Gotchas encountered

- **`deploy-pages` needs Pages pre-enabled** with `build_type=workflow`. Enabled it via the API up front;
  otherwise the first deploy job errors with "Pages not enabled."
- **`read_only=True` on the report's DuckDB connection** so it can run right after `dbt build` without
  fighting for the single-writer lock.
- **The public Pages URL must be checked before the README says "deployed."** Per the honesty rule, the
  word "deployed" waits until the live URL actually returns the lineage page (verified at Step 8).

---

## What's next (Step 8 preview)

**Step 8 — finalize.** Fill the README metrics table with real measured numbers (model/test counts,
pass-rate, build time, rows, SCD2 versions), write the honest-limitations section (static-seed freshness,
single-writer DuckDB, the documented-not-run cloud/MWAA promotion path), add the headline finding + the
live Pages link (after verifying it loads), and pin everything.
