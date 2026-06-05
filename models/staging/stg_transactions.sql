-- One cleaned row per transaction. Rename + type only; no business logic.
with source as (
    select * from {{ source('raw', 'transactions') }}
)

select
    transaction_id,
    date            as transaction_date,
    account_id,
    merchant_id,
    name            as description,
    amount,
    amount < 0      as is_inflow,        -- negative = money in (payroll, card payment)
    abs(amount)     as abs_amount,
    pending,
    _loaded_at
from source
