# Step 9 — Adversarial review + fixes (2026-06-05)

After the 8-step build shipped, four independent review agents audited the whole repo — **correctness**,
**honesty**, **recruiter-credibility**, and a true **clean-clone reproducibility** test. This note records
what they found and what changed.

> New term? See [`glossary.md`](./glossary.md).

---

## What the review found

- **Reproducible: YES.** A fresh `git clone` of the public repo, following the README verbatim, built green
  (`PASS=54`) and reproduced the SCD2 history (46 versions / 6 closed) on a clean machine. Every README
  number verified true on the clone.
- **Correctness: no real bugs.** The date spine covers the data exactly, surrogate keys line up, `check_cols`
  correctly excludes `_loaded_at` (so loads don't spuriously version every merchant), contract types match.
- **Honesty: one real overclaim** (fixed below).
- **Recruiter: would interview.** Top gap flagged: no incremental model (tracked as a follow-up).

---

## Fixes applied this step

1. **Honesty — the headline count.** The README claimed the injected bad row passed "all **12** generic +
   expectation tests." There are only **11** generic/expectation tests on the fact; the 12th passing test
   was the *other singular* test. Reworded README + `notes/step-06` + the INDEX finding to: *12 of 13 passed
   — 11 generic/expectation + one singular — only `assert_inflow_categories_are_negative` caught it.*
2. **Stronger SCD2 invariant.** `assert_one_current_merchant_version` only caught *duplicate* current
   versions; it now asserts **exactly one** open version per merchant (`<> 1`), catching a lost-current bug
   (zero open) too.
3. **Removed a redundant test.** `transaction_key` had both a contract `not_null` constraint and a
   `not_null` data test — dropped the data test (kept `unique`). Test count 45 → 44.
4. **Removed dead config.** `dbt_project.yml` declared an `intermediate` model layer with no models, which
   printed an "unused configuration path" warning every run — removed.
5. **`month` is now a DATE.** `date_trunc` returns a timestamp in DuckDB; cast the monthly mart's grain
   column to `date` so the grain is clean for BI.
6. **Forward-compatible package.** `calogica/dbt_expectations` redirects (deprecation warning) to
   `metaplane/dbt_expectations` — updated the package name so it keeps installing after the redirect is
   removed.
7. **README quickstart note.** Flagged that `dbt docs serve` runs a *blocking* server (Ctrl-C to stop), and
   that `--static` lets you just open `target/static_index.html` — so a newcomer doesn't think it hung.

After fixes: clean rebuild → **PASS=53, ERROR=0** (44 tests + 8 models + 1 snapshot), SCD2 46/6/40 intact.

---

## Tracked follow-up (not done here)

- **Incremental model.** The sharpest interview gap: every model is full-refresh. The honest version needs a
  late-arriving "append" scenario so the incremental path is *exercised* in CI (not configured-but-unrun) —
  a real next iteration, tracked in the career hub rather than rushed at review time.
- **Lineage-graph screenshot in the README** (the live Pages site already exists; a static PNG would put the
  DAG in the 30-second scan).

---

## The discipline worth remembering

The most valuable finds were a **reproducibility proof** (a clone really works) and a **single honest-count
error** a sharp interviewer could have caught. Neither was a code bug — both were about whether the *claims*
match reality. That's exactly what an adversarial pass is for.
