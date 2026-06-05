-- Merchant dimension (current view). Grain: one row per merchant.
-- Historical versions of these attributes are tracked by the SCD2 snapshot (Step 5).
select
    {{ dbt_utils.generate_surrogate_key(['merchant_id']) }} as merchant_key,
    merchant_id,
    merchant_name,
    category_primary,
    category_sub,
    city
from {{ ref('stg_merchants') }}
