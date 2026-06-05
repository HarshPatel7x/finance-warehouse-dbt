-- Business rule: inflow-only categories (payroll, card payments) must be money IN,
-- i.e. amount < 0. A POSITIVE amount on a payroll/card merchant is a classification
-- error. This row would still pass unique, not_null, relationships, accepted_values,
-- and the value-range expectation — only this singular test catches it.
select
    f.transaction_id,
    m.category_sub,
    f.amount
from {{ ref('fct_transactions') }} f
join {{ ref('dim_merchant') }} m on f.merchant_key = m.merchant_key
where m.category_sub in ('Payroll', 'Credit Card')
  and f.amount > 0
