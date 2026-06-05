-- One cleaned row per merchant (the SCD2 dimension source).
with source as (
    select * from {{ source('raw', 'merchants') }}
)

select
    merchant_id,
    merchant_name,
    category_primary,
    category_sub,
    city,
    _loaded_at
from source
