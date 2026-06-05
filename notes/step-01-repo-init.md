# Step 1 — Repo init + dbt skeleton (2026-06-05)

Compiled at the close of Step 1. From `mkdir` to first push: dbt project that `dbt debug`-passes on a
clean Python 3.12 venv, wired for CI and PR-per-step.

> New to a term (warehouse, ELT, dbt, source, materialization)? See [`glossary.md`](./glossary.md).

---

## What we built

```
finance-warehouse-dbt/
├── .gitignore              # skip venv, target/, dbt_packages/, *.duckdb, logs/
├── requirements.txt        # dbt-duckdb==1.10.1 + dbt-core==1.11.11 (Python 3.12 only)
├── dbt_project.yml         # project config — model layers + materializations
├── profiles.yml            # in-repo DuckDB connection (--profiles-dir .)
├── packages.yml            # dbt_utils + dbt_expectations
├── README.md               # front door — mermaid + TARGET metrics + sibling links
├── .github/workflows/ci.yml# PR gate (deps + parse now; build added with models)
└── notes/                  # INDEX + glossary + this retro
```

`dbt deps` → installed both packages. `dbt debug --profiles-dir .` → **All checks passed!** (DuckDB
adapter 1.10.1, connection ok).

---

## Concepts taught (beginner language)

### 1. Why a Python **3.12** venv, not the system 3.14
dbt does not support Python 3.14 yet — it installs but **crashes at import** (`mashumaro`/`pydantic.v1`
incompatibility, dbt-core issue #12098). The machine's default `python3` is 3.14, so a fresh clone that
runs `pip install dbt-duckdb` under 3.14 would crash. Fix: pin a **3.12** venv and say so loudly in the
README + `requirements.txt` + CI (`python-version: "3.12"`). Same pin the sibling lakehouse repo uses.

### 2. `dbt_project.yml` is the project's config
Names the project, points at the **profile** (the connection), and sets where each layer materializes:
staging/intermediate as cheap **views**, marts as **tables**. dbt reads this to know how to build.

### 3. In-repo `profiles.yml` + `--profiles-dir .`
By default dbt looks for the connection in `~/.dbt/profiles.yml` (global, per-user). For a clone-and-run
portfolio repo that's a trap — a recruiter cloning it has no such file. Putting `profiles.yml` in the repo
and always passing `--profiles-dir .` makes the project self-contained: **zero global setup**.

### 4. `packages.yml` + `dbt deps`
Third-party dbt packages (here `dbt_utils` for surrogate keys/tests and `dbt_expectations` for richer
data-quality tests). `dbt deps` downloads them into `dbt_packages/` (gitignored — rebuilt on clone).

### 5. The DuckDB file IS the warehouse
`type: duckdb, path: finance_warehouse.duckdb`. The entire "warehouse" is one local file, gitignored
because it's rebuilt from the loader + `dbt build`. No server, no Docker, no cloud — same SQL as Snowflake.

---

## Decisions locked (from the 3-agent adversarial plan)

1. **Python 3.12 venv** — non-negotiable (3.14 breaks dbt).
2. **dbt-duckdb**, not Snowflake/BigQuery — $0, embedded, identical modeling skills, runs in CI with no
   secrets.
3. **dbt_expectations**, not Great Expectations — same expectation-style tests, no separate runtime; the
   resume line gets reconciled to match at the end.
4. **Public repo** — so the `dbt docs` lineage site can deploy on free GitHub Pages (2 of 3 sibling repos
   are already public).
5. **PR-per-step** with a local `pre-push` hook blocking direct pushes to `main`.

---

## Gotchas encountered

- **`PackageRedirectDeprecation` warning on `dbt deps`.** `dbt-labs/dbt_utils` and `calogica/dbt_expectations`
  now redirect to dbt's new package hub. It's a *warning* — install still succeeds — but worth migrating the
  package names in a later step to silence it.
- **PEP-668 externally-managed environment.** Homebrew Python refuses a bare `pip install`. The venv is
  mandatory regardless of the dbt-version issue.
- **Nested repo hygiene.** `~/Desktop/Harsh/` is itself a git repo; added `finance-warehouse-dbt/` to its
  `.gitignore` (alongside the three sibling repos) so the new repo's files don't pollute the parent's
  `git status`.

---

## Snippets worth remembering

### Self-contained dbt run (no global config)
```bash
dbt deps  --profiles-dir .
dbt debug --profiles-dir .
dbt build --profiles-dir .
```

### The Python-3.12 pin (README + CI)
```bash
python3.12 -m venv venv   # NOT 3.14 — dbt-core #12098
```
```yaml
# .github/workflows/ci.yml
- uses: actions/setup-python@v5
  with: { python-version: "3.12" }
```

---

## What's next (Step 2 preview)

**Step 2 — synthetic generator + raw load.** Expand the shared seed=42 corpus to ~40k rows over 24 months
across multiple accounts + merchants with **time-varying** attributes (so SCD2 has real changes to capture),
load it into the DuckDB `raw` schema with a real `_loaded_at` UTC stamp, and declare it as a dbt **source**
with a freshness check.
