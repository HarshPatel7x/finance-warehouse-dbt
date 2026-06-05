-- Business rule a generic test can't express: no transaction may be dated in the
-- future. Returns any offending rows (a future-dated txn would still pass unique,
-- not_null, relationships, and accepted_values — only this catches it).
select
    transaction_id,
    transaction_date
from {{ ref('fct_transactions') }}
where transaction_date > current_date
