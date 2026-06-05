{% snapshot snap_merchant %}
{{
    config(
        target_schema='snapshots',
        unique_key='merchant_id',
        strategy='check',
        check_cols=['merchant_name', 'category_primary', 'category_sub', 'city'],
    )
}}
-- SCD Type 2 history of the merchant dimension. Each run, if any check_col changed
-- for a merchant_id, dbt closes the old version (dbt_valid_to = now) and opens a new
-- one. Exercised by reloading scenario v2 (mutated merchants) — see notes/step-05.
select
    merchant_id,
    merchant_name,
    category_primary,
    category_sub,
    city,
    _loaded_at
from {{ source('raw', 'merchants') }}
{% endsnapshot %}
