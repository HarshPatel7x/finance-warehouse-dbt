-- SCD2 invariant: every merchant has exactly ONE open (current) version in the
-- snapshot. If this returns any rows, history is corrupt (two rows both claim to be
-- "now"). A singular test — returns the offending merchant_ids.
select
    merchant_id,
    count(*) as open_versions
from {{ ref('snap_merchant') }}
where dbt_valid_to is null
group by merchant_id
having count(*) > 1
