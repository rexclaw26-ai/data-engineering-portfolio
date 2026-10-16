# Commerce Analytics Warehouse

A reproducible SQL + Python data-modeling project that turns fictional order records into a SQLite **star schema**, consisting of `dim_customer`, `dim_product`, and `fact_order`. It uses unique order IDs to prevent double counting and stores money as integer cents.

**Built in this repository:** Real runnable demo, not an unimplemented idea.

## Run

From the repository root:

```bash
python projects/commerce-warehouse/build.py --db /tmp/commerce-demo.sqlite
```

The sample data loads 6 orders totaling **$273.46**, with August revenue of **$109.47** and September revenue of **$163.99**. Running the script again against the same database inserts no duplicate facts.

## Files

- `build.py`: parse, validate, and load orders into a SQLite warehouse
- `schema.sql`: fact and dimension table definitions with foreign keys
- `monthly_revenue.sql`: monthly revenue by product category
- `sample_orders.csv`: six fictional orders
- `../../tests/test_projects.py`: repeatable integration tests

**What it demonstrates:** Dimensional modeling, SQL joins and aggregations, incremental/idempotent loads, and revenue accuracy.
