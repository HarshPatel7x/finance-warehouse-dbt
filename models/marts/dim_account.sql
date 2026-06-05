-- Account dimension. Grain: one row per account. Surrogate key for clean joins.
select
    {{ dbt_utils.generate_surrogate_key(['account_id']) }} as account_key,
    account_id,
    account_name,
    account_type,
    open_date
from {{ ref('stg_accounts') }}
