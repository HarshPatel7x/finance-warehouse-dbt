-- Date dimension covering the corpus range. Grain: one row per calendar day.
-- date_key is a yyyymmdd integer so the fact can carry a compact FK.
with spine as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2023-06-01' as date)",
        end_date="cast('2025-06-01' as date)"
    ) }}
)

select
    cast(strftime(date_day, '%Y%m%d') as integer) as date_key,
    date_day                                      as full_date,
    extract(year    from date_day)                as year,
    extract(quarter from date_day)                as quarter,
    extract(month   from date_day)                as month,
    strftime(date_day, '%Y-%m')                   as year_month,
    strftime(date_day, '%B')                      as month_name,
    extract(day     from date_day)                as day_of_month,
    extract(dow     from date_day)                as day_of_week,
    extract(dow from date_day) in (0, 6)          as is_weekend
from spine
