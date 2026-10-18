"""Run SQL and Python data-quality checks on a customer CSV (stdlib only)."""
import argparse
import csv
import json
import re
import sqlite3
import subprocess
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
    duplicate_set = set(duplicate_ids)

    missing_emails = 0
    invalid_emails = 0
    invalid_dates = 0
    negative_or_invalid_balances = 0

    failed_records = []
    for idx, row in enumerate(rows, start=2):
        issues = []
        cid = row["customer_id"].strip()
        email = row["email"].strip()
        signup = row["signup_date"].strip()
        bal = row["balance"].strip()

        if not cid:
            issues.append({"rule": "missing_customer_ids", "message": "Customer ID is missing"})
        elif cid in duplicate_set:
            issues.append({"rule": "duplicate_customer_ids", "message": f"Duplicate customer_id '{cid}'"})

        if not email:
            missing_emails += 1
            issues.append({"rule": "missing_emails", "message": "Email is missing"})
        elif not EMAIL_PATTERN.fullmatch(email):
            invalid_emails += 1
            issues.append({"rule": "invalid_email_format", "message": f"Invalid email '{row['email']}'"})

        try:
            date.fromisoformat(signup)
        except ValueError:
            invalid_dates += 1
            issues.append({"rule": "invalid_signup_dates", "message": f"Invalid signup_date '{row['signup_date']}'"})

        try:
            amount = Decimal(bal)
            if not amount.is_finite() or amount < 0:
                negative_or_invalid_balances += 1
                issues.append({"rule": "invalid_or_negative_balances", "message": f"Invalid/negative balance '{row['balance']}'"})
        except (InvalidOperation, ValueError):
            negative_or_invalid_balances += 1
            issues.append({"rule": "invalid_or_negative_balances", "message": f"Invalid balance '{row['balance']}'"})

        if issues:
            why = "; ".join(i["message"] for i in issues)
            failed_records.append({
                "row_number": idx,
                "customer_id": row["customer_id"],
                "email": row["email"],
                "signup_date": row["signup_date"],
                "balance": row["balance"],
                "issues": [i["rule"] for i in issues],
                "issue_details": why,
            })

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
        "failed_records": failed_records,
        "failed_count": len(failed_records),
    }


def sync_to_sheet(report, sheet_id):
    summary_vals = [["rule", "failures", "examples"]]
    for c in report["checks"]:
        summary_vals.append([c["rule"], c["failures"], ", ".join(c.get("examples", []))])
    summary_vals.append([])
    summary_vals.append(["file", report["file"]])
    summary_vals.append(["rows_checked", report["rows_checked"]])
    summary_vals.append(["passed", str(report["passed"])])
    summary_vals.append(["failed_records", report["failed_count"]])

    header = ["row_number", "customer_id", "email", "signup_date", "balance", "issues", "whats_wrong"]
    failed_vals = [header]
    for r in report["failed_records"]:
        failed_vals.append([
            r["row_number"],
            r["customer_id"],
            r["email"],
            r["signup_date"],
            r["balance"],
            ", ".join(r["issues"]),
            r["issue_details"],
        ])
    if len(failed_vals) == 1:
        failed_vals.append(["(no failures - all records passed)", "", "", "", "", "", ""])

    payload = {
        "valueInputOption": "RAW",
        "data": [
            {"range": f"summary!A1:C{len(summary_vals)}", "values": summary_vals},
            {"range": f"failed_records!A1:G{len(failed_vals)}", "values": failed_vals},
        ]
    }
    cmd = ["gws", "sheets", "spreadsheets", "values", "batchUpdate", "--params", json.dumps({"spreadsheetId": sheet_id}), "--json", json.dumps(payload), "--format", "json"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        raise SystemExit(result.returncode)
    print(result.stdout[:2000])
    print(f"Synced to https://docs.google.com/spreadsheets/d/{sheet_id}/edit")
    print(f"  summary: {len(summary_vals)} rows, failed_records: {len(failed_vals)-1} records")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", nargs="?", type=Path, default=HERE / "sample_customers.csv")
    parser.add_argument("--output", type=Path, help="Optional path for JSON report")
    parser.add_argument("--sheet-id", type=str, help="Optional Google Sheet ID to push detailed findings")
    parser.add_argument("--create-sheet", action="store_true", help="Create a new Google Sheet and push findings there")
    args = parser.parse_args()
    report = check_csv(args.csv)
    output = json.dumps(report, indent=2)
    print(output)
    if args.output:
        args.output.write_text(output + "\n", encoding="utf-8")

    sheet_id = args.sheet_id
    if args.create_sheet:
        create_cmd = ["gws", "sheets", "spreadsheets", "create", "--json", json.dumps({"properties": {"title": f"Data Quality Report - {report['file']}"}, "sheets": [{"properties": {"title": "summary"}}, {"properties": {"title": "failed_records"}}]}), "--format", "json"]
        res = subprocess.run(create_cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(res.stdout)
            print(res.stderr)
            raise SystemExit(res.returncode)
        data = json.loads(res.stdout)
        sheet_id = data.get("spreadsheetId")
        print(f"Created new sheet: https://docs.google.com/spreadsheets/d/{sheet_id}/edit")

    if sheet_id:
        sync_to_sheet(report, sheet_id)

    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
