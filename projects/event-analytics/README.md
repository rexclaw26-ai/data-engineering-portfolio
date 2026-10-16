# Event Analytics ELT Pipeline

A working Python and SQL pipeline that loads event CSV data into SQLite, rejects malformed records, and builds daily engagement and revenue metrics.

**Built in this repository:** Not a conceptual project. No third-party packages required.

## Run

From the repository root:

```bash
python projects/event-analytics/pipeline.py --db /tmp/event-demo.sqlite
```

The script ingests 7 unique valid events, flags 1 duplicate and rejects 1 invalid revenue row. Its daily report includes $44.49 revenue on October 1 and $40.00 on October 2, for **$84.49** total.

Run it again using the same database to demonstrate idempotent ingestion (0 additional rows). The SQLite database is saved at the path supplied through `--db`.

## Files

- `pipeline.py`: timestamp validation, amount conversion to cents, duplicate-aware loading
- `sample_events.csv`: fictional demo input with duplicate and invalid event
- `daily_metrics.sql`: aggregation query for daily active users, events, purchases, revenue
- `../../tests/test_projects.py`: automated behavior tests

**What it demonstrates:** Python ingestion, validation, SQL aggregations, money-safe storage, and repeatable loads.
