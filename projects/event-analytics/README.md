# Event Analytics ELT Pipeline

A working Python and SQL pipeline that loads event CSV data into SQLite, rejects malformed records, builds daily, weekly, and top-event metrics, and syncs to Google Sheets.

**Built in this repository:** Not a conceptual project. No third-party packages required.

## Run

From the repository root:

```bash
python projects/event-analytics/pipeline.py --db /tmp/event-demo.sqlite
```

The script ingests 7 unique valid events, flags 1 duplicate and rejects 1 invalid revenue row. Its daily report includes $44.49 revenue on October 1 and $40.00 on October 2, for **$84.49** total.

Run it again using the same database to demonstrate idempotent ingestion (0 additional rows, counted as `duplicates`). Corrections are applied automatically: if a row with the same `event_id` arrives with different field values after passing the same validation, the existing row is updated and counted as `updated` (identical replays remain `duplicates`).

```bash
python projects/event-analytics/pipeline.py --db /tmp/event-demo.sqlite --input new_events.csv
python projects/event-analytics/sync_to_sheets.py --db /tmp/event-demo.sqlite
```

The SQLite database is saved at the path supplied through `--db`. Use the same `--db` for incremental loads and for the sync step so new `event_id`s are inserted, corrections are updated, and the Sheets dashboards reflect the current state.

## Files

- `pipeline.py`: timestamp validation, amount conversion to cents, duplicate-aware and correction-aware loading (`inserted`/`updated`/`duplicates`/`rejected`)
- `sample_events.csv`: fictional demo input with duplicate and invalid event
- `daily_metrics.sql`: aggregation query for daily active users, events, purchases, revenue
- `weekly_metrics.sql`: same metrics aggregated by ISO week (`YYYY-WXX`)
- `top_events.sql`: frequency by `event_type`, most common first
- `sync_to_sheets.py`: reads the three SQL files and writes `daily`, `weekly`, `top_events` tabs via Sheets API (range sized to current data so charts auto-update)
- `../../tests/test_projects.py`: automated behavior tests

**What it demonstrates:** Python ingestion, validation, SQL aggregations, money-safe storage, repeatable and correction-aware loads, and automated Sheets reporting.
