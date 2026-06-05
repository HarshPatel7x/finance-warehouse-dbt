-- One cleaned row per account.
with source as (
    select * from {{ source('raw', 'accounts') }}
)

select
    account_id,
    account_name,
    account_type,
    open_date
from source
