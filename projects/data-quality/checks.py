"""Run SQL and Python data-quality checks on a customer CSV (stdlib only)."""
import argparse
import csv
import json
import re
import sqlite3
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

HERE = Path(__file__).resolve().parent
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def check_csv(csv_path):
    with open(csv_path, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    with sqlite3.connect(":memory:") as db:
        db.execute("CREATE TABLE stage (customer_id TEXT, email TEXT, signup_date TEXT, balance TEXT)")
        db.executemany(
            "INSERT INTO stage VALUES (?, ?, ?, ?)",
            [(r["customer_id"], r["email"], r["signup_date"], r["balance"]) for r in rows]
        )
        duplicate_ids = [
            r[0] for r in db.execute(
                "SELECT customer_id FROM stage WHERE TRIM(customer_id) != '' "
                "GROUP BY customer_id HAVING COUNT(*) > 1 ORDER BY customer_id"
            )
        ]
        missing_ids = db.execute(
            "SELECT COUNT(*) FROM stage WHERE TRIM(customer_id) = ''"
        ).fetchone()[0]
    missing_emails = sum(not row["email"].strip() for row in rows)
    invalid_emails = sum(
        bool(row["email"].strip()) and not EMAIL_PATTERN.fullmatch(row["email"].strip())
        for row in rows
    )
    invalid_dates = 0
    negative_or_invalid_balances = 0
    for row in rows:
        try:
            date.fromisoformat(row["signup_date"].strip())
        except ValueError:
            invalid_dates += 1
        try:
            amount = Decimal(row["balance"].strip())
            if not amount.is_finite() or amount < 0:
                negative_or_invalid_balances += 1
        except InvalidOperation:
            negative_or_invalid_balances += 1

    results = [
        {"rule": "duplicate_customer_ids", "failures": len(duplicate_ids), "examples": duplicate_ids[:5]},
        {"rule": "missing_customer_ids", "failures": missing_ids},
        {"rule": "missing_emails", "failures": missing_emails},
        {"rule": "invalid_email_format", "failures": invalid_emails},
        {"rule": "invalid_signup_dates", "failures": invalid_dates},
        {"rule": "invalid_or_negative_balances", "failures": negative_or_invalid_balances},
    ]
    return {
        "file": Path(csv_path).name,
        "rows_checked": len(rows),
        "passed": all(item["failures"] == 0 for item in results),
        "checks": results,
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", nargs="?", type=Path, default=HERE / "sample_customers.csv")
    parser.add_argument("--output", type=Path, help="Optional path for JSON report")
    args = parser.parse_args()
    report = check_csv(args.csv)
    output = json.dumps(report, indent=2)
    print(output)
    if args.output:
        args.output.write_text(output + "\n", encoding="utf-8")
    raise SystemExit(0 if report["passed"] else 1)

if __name__ == "__main__":
    main()
