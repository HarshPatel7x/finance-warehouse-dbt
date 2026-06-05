# Glossary — analytics engineering, in plain words

Read top-down: each concept builds on the last. These are the ideas this repo demonstrates in code.

### 1. Data warehouse
A database tuned for *analytics* (big scans, aggregations) rather than fast single-row app writes. Here
the whole warehouse is one embedded **DuckDB** file — no server, no cloud. Same SQL ideas as Snowflake or
BigQuery, just on a laptop.

### 2. ETL vs ELT
**ETL** = Extract, Transform, then Load (transform before it lands). **ELT** = Extract, Load the raw data
first, then Transform *inside* the warehouse with SQL. dbt is an ELT tool: raw data lands in DuckDB, then
dbt builds clean tables from it. ELT wins when storage is cheap and the warehouse is powerful.

### 3. dbt (data build tool)
A tool that lets you write each transformation as a `SELECT` statement in a `.sql` file (a **model**). dbt
figures out the order to run them, turns them into tables/views, and runs **tests** on the results. It's
the most-listed tool in data-engineering job posts because it brings software discipline (version control,
tests, docs, CI) to SQL.

### 4. Source vs seed
A **source** is raw data already in the warehouse that dbt reads but doesn't create (here: the `raw`
transactions our loader writes). A **seed** is a small CSV dbt itself loads. We use a loader + source (not
a seed) because the dataset is large and we stamp a real load timestamp on it.

### 5. Staging → intermediate → marts (the medallion / layered pattern)
- **Staging:** one cleaned model per source table — rename columns, fix types, no business logic. Cheap
  **views**.
- **Intermediate:** optional middle steps that join or reshape.
- **Marts:** the final tables an analyst or BI tool queries — modeled for a question, materialized as
  **tables**. (Bronze/Silver/Gold is the same idea under different names.)

### 6. Materialization (view / table / incremental)
How dbt persists a model. A **view** is a saved query (cheap, always fresh). A **table** is computed and
stored (fast to read). An **incremental** model only processes new rows each run (for big, append-heavy
data). We use views for staging, tables for marts.

### 7. Star schema: fact and dimension tables
A modeling shape. A **fact** table holds the events/measurements (one row per transaction, with amounts).
**Dimension** tables hold the descriptive context (the account, the merchant, the date). The fact points at
each dimension by key — drawn out, it looks like a star. It makes "spend by merchant by month" a simple,
fast join.

### 8. Grain
The exact thing one row of a table represents — e.g. "one row per transaction." Declaring the grain up
front (and testing it with a uniqueness check) is the single most important modeling decision; bugs almost
always trace back to a fuzzy grain.

### 9. Surrogate key
A stable, generated id for a dimension row (e.g. a hash of the natural key), instead of relying on a messy
real-world id. dbt_utils' `generate_surrogate_key` builds them. They make joins and SCD2 history clean.

### 10. SCD Type 2 (Slowly Changing Dimension)
A way to keep **history** when a dimension attribute changes. Instead of overwriting (that's Type 1), you
close the old row (`valid_to = now`) and open a new version (`valid_from = now`, `is_current = true`). So
you can answer "what category was this merchant in *back then*?" — not just today.

### 11. Snapshot
dbt's built-in SCD2 machine. You point it at a table and a set of columns; each run, if those columns
changed for a key, dbt closes the old version and writes a new one. It only shows real history if the
source data actually changes between runs (so we reload a mutated v2 to exercise it).

### 12. Generic vs singular test
- **Generic test:** a reusable rule applied via YAML — `not_null`, `unique`, `accepted_values`,
  `relationships` (foreign-key integrity).
- **Singular test:** a one-off `SELECT` in `tests/` that returns the *bad* rows; if it returns any, the
  test fails. For business rules generic tests can't express (e.g. "no transaction dated in the future").
A green generic suite can still hide a bad row — that's why singular tests matter.

### 13. dbt-expectations
A dbt package of richer tests (value ranges, distributions, row-count bounds) modeled on the Python
**Great Expectations** library — but running entirely inside dbt with no extra runtime. The free,
in-stack way to assert "amounts are between X and Y" or "this table has at least N rows."

### 14. Model contract
A promise about a model's shape — exact column names, types, and constraints — declared in YAML and
**enforced** by dbt at build time. If a model's output drifts from its contract, the build fails. This is
how "data contracts between the mart layer and downstream BI" become real, not just a doc.

### 15. Source freshness
A check on how stale a source is: dbt looks at a load-timestamp column and warns/errors if the newest row
is older than a threshold (the **freshness SLA**). Meaningful only when something keeps loading the source;
on a one-shot static seed it's trivially fresh — honest framing matters.

### 16. Exposure
A dbt object that names a **downstream consumer** of your models (a dashboard, a report, an analysis). It
makes the lineage graph end in a real *use*, and lets you see what breaks if an upstream model changes.

### 17. Lineage / DAG
The dependency graph dbt builds from your `ref()`/`source()` calls — a **DAG** (directed acyclic graph)
from raw → staging → marts → exposure. `dbt docs` renders it as a clickable map. Lineage is how you answer
"if I change this, what's affected?"

### 18. CI gate
Continuous Integration: on every pull request, a clean machine installs deps, builds the warehouse, and
runs all tests. The PR can't merge unless it's green. Here it runs with **zero secrets** — strong evidence
that anyone can clone and reproduce the whole thing.
