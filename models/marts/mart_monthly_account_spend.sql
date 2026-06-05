-- Monthly spend rollup per account — the BI-facing mart (the downstream consumer
-- in Step 7's exposure reads this). Grain: one row per account per month.
with f as (
    select * from {{ ref('fct_transactions') }}
)

select
    account_key,
    date_trunc('month', transaction_date)                      as month,
    count(*)                                                   as txn_count,
    sum(case when not is_inflow then abs_amount else 0 end)    as total_outflow,
    sum(case when is_inflow     then abs_amount else 0 end)    as total_inflow,
    sum(amount)                                                as net_amount
from f
group by 1, 2
