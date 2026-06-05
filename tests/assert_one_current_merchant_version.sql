-- SCD2 invariant: every merchant has EXACTLY one open (current) version in the
-- snapshot. Catches both duplicates (>1 open) AND a lost-current bug (0 open).
-- Returns any merchant whose open-version count isn't exactly 1.
select
    merchant_id,
    count(*) filter (where dbt_valid_to is null) as open_versions
from {{ ref('snap_merchant') }}
group by merchant_id
having count(*) filter (where dbt_valid_to is null) <> 1
