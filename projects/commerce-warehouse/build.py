"""Build a small analytical star schema for fictional order data (stdlib only)."""
import argparse
import csv
import sqlite3
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

HERE = Path(__file__).resolve().parent

def parse_order(row):
    order_id, customer_id, product_id = (row[key].strip() for key in ("order_id", "customer_id", "product_id"))
    region, category = (row[key].strip().lower() for key in ("region", "category"))
    if not all((order_id, customer_id, product_id, region, category)):
        raise ValueError("Missing key or dimension")
    day = date.fromisoformat(row["ordered_at"].strip()).isoformat()
    quantity = int(row["quantity"])
    unit_price = Decimal(row["unit_price"].strip())
    if quantity <= 0 or not unit_price.is_finite() or unit_price < 0 or unit_price.as_tuple().exponent < -2:
        raise ValueError("Invalid quantity or unit price")
    cents = int(unit_price * 100)
    return order_id, day, customer_id, region, product_id, category, quantity, cents

def build(csv_path, db_path):
    stats = {"inserted": 0, "duplicates": 0, "rejected": 0}
    with sqlite3.connect(db_path) as db:
        db.execute("PRAGMA foreign_keys = ON")
        db.executescript((HERE / "schema.sql").read_text(encoding="utf-8"))
        with open(csv_path, newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                try:
                    order_id, day, customer, region, product, category, qty, cents = parse_order(row)
                except (ValueError, KeyError, InvalidOperation, AttributeError):
                    stats["rejected"] += 1
                    continue
                db.execute("INSERT OR IGNORE INTO dim_customer VALUES (?, ?)", (customer, region))
                db.execute("INSERT OR IGNORE INTO dim_product VALUES (?, ?)", (product, category))
                cur = db.execute(
                    "INSERT OR IGNORE INTO fact_order VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (order_id, day, customer, product, qty, cents, qty * cents)
                )
                stats["inserted" if cur.rowcount else "duplicates"] += 1
        db.commit()
    return stats

def monthly_revenue(db_path):
    with sqlite3.connect(db_path) as db:
        return db.execute((HERE / "monthly_revenue.sql").read_text(encoding="utf-8")).fetchall()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=HERE / "sample_orders.csv")
    parser.add_argument("--db", type=Path, default=HERE / "commerce.sqlite")
    args = parser.parse_args()
    print("Loaded:", build(args.input, args.db))
    print("month | category | orders | revenue_usd")
    for row in monthly_revenue(args.db):
        print(" | ".join(str(value) for value in row))

if __name__ == "__main__":
    main()
