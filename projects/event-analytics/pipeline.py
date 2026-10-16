"""Idempotent event-ingestion pipeline using Python and SQLite (stdlib only)."""
import argparse
import csv
import sqlite3
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

HERE = Path(__file__).resolve().parent
ALLOWED_EVENTS = {"page_view", "add_to_cart", "purchase"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    occurred_at TEXT NOT NULL,
    event_date TEXT NOT NULL,
    user_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    revenue_cents INTEGER NOT NULL CHECK (revenue_cents >= 0)
);
"""

def normalize(row):
    event_id = row["event_id"].strip()
    user_id = row["user_id"].strip()
    event_type = row["event_type"].strip().lower()
    if not event_id or not user_id or event_type not in ALLOWED_EVENTS:
        raise ValueError("Missing ID or unsupported event type")
    try:
        timestamp = datetime.fromisoformat(row["occurred_at"].strip().replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            raise ValueError("Event timestamp must include timezone")
        timestamp = timestamp.astimezone(timezone.utc)
        amount = Decimal(row["revenue"].strip())
        if not amount.is_finite() or amount < 0 or amount.as_tuple().exponent < -2:
            raise ValueError("Revenue must be a nonnegative currency amount")
        cents = int(amount * 100)
    except (InvalidOperation, ValueError, OverflowError) as exc:
        raise ValueError("Invalid timestamp or revenue") from exc
    if (event_type == "purchase" and cents <= 0) or (event_type != "purchase" and cents != 0):
        raise ValueError("Purchase requires revenue; non-purchase cannot have revenue")
    return event_id, timestamp.isoformat(), timestamp.date().isoformat(), user_id, event_type, cents

def load_events(csv_path, db_path):
    stats = {"inserted": 0, "duplicates": 0, "rejected": 0}
    with sqlite3.connect(db_path) as db:
        db.execute(SCHEMA)
        with open(csv_path, newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                try:
                    values = normalize(row)
                except (ValueError, KeyError, AttributeError):
                    stats["rejected"] += 1
                    continue
                cursor = db.execute(
                    "INSERT OR IGNORE INTO events VALUES (?, ?, ?, ?, ?, ?)", values
                )
                stats["inserted" if cursor.rowcount else "duplicates"] += 1
        db.commit()
    return stats

def daily_metrics(db_path):
    with sqlite3.connect(db_path) as db:
        query = (HERE / "daily_metrics.sql").read_text(encoding="utf-8")
        return db.execute(query).fetchall()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=HERE / "sample_events.csv")
    parser.add_argument("--db", type=Path, default=HERE / "events.sqlite")
    args = parser.parse_args()
    stats = load_events(args.input, args.db)
    print("Ingested:", stats)
    print("date | events | unique_users | purchases | revenue_usd")
    for row in daily_metrics(args.db):
        print(" | ".join(str(value) for value in row))

if __name__ == "__main__":
    main()
