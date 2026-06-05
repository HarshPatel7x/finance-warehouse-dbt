-- Transaction fact. Grain: ONE row per transaction. Carries surrogate FKs to every
-- dimension + the additive measures (amount). This is the table BI tools query.
with t as (
    select * from {{ ref('stg_transactions') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['transaction_id']) }} as transaction_key,
    transaction_id,
    {{ dbt_utils.generate_surrogate_key(['account_id']) }}     as account_key,
    {{ dbt_utils.generate_surrogate_key(['merchant_id']) }}    as merchant_key,
    cast(strftime(transaction_date, '%Y%m%d') as integer)      as date_key,
    transaction_date,
    amount,
    abs_amount,
    is_inflow,
    pending
from t
