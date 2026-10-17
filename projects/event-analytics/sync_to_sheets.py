"""Sync Event Analytics SQLite metrics to Google Sheets (daily/weekly/top_events).

Idempotent: re-runs insert only new event_ids (INSERT OR IGNORE).
Usage:
  python projects/event-analytics/pipeline.py --db /tmp/event-demo.sqlite --input new_events.csv
  python projects/event-analytics/sync_to_sheets.py --db /tmp/event-demo.sqlite --sheet-id 16Y_vEmjqVCkXM5rnkTQXUTfZv_vM3OAGwn8mtTuGIaY

Reads the three SQL files (daily_metrics.sql, weekly_metrics.sql, top_events.sql) so
future report changes stay in sync — no hard-coded queries.
"""
import argparse
import json
import sqlite3
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent

def fetch(db, sql_file):
    return sqlite3.connect(db).execute(Path(HERE / sql_file).read_text()).fetchall()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", type=Path, required=True, help="SQLite DB path (use same --db as pipeline.py)")
    p.add_argument("--sheet-id", type=Path, required=False, default=Path("16Y_vEmjqVCkXM5rnkTQXUTfZv_vM3OAGwn8mtTuGIaY"))
    args = p.parse_args()
    db = str(args.db)
    sheet_id = str(args.sheet_id)
    daily = fetch(db, "daily_metrics.sql")
    weekly = fetch(db, "weekly_metrics.sql")
    top = fetch(db, "top_events.sql")
    # Build values with headers
    daily_vals = [["event_date","event_count","unique_users","purchases","revenue_usd"]] + [list(r) for r in daily]
    weekly_vals = [["week","event_count","unique_users","purchases","revenue_usd"]] + [list(r) for r in weekly]
    top_vals = [["event_type","event_count"]] + [list(r) for r in top]
    # Clear and write ranges sized to current data (headers + rows)
    # Use gws CLI — requires gws auth already configured
    daily_range = f"daily!A1:E{len(daily_vals)}"
    weekly_range = f"weekly!A1:E{len(weekly_vals)}"
    top_range = f"top_events!A1:B{len(top_vals)}"
    payload = {
        "valueInputOption": "RAW",
        "data": [
            {"range": daily_range, "values": daily_vals},
            {"range": weekly_range, "values": weekly_vals},
            {"range": top_range, "values": top_vals},
        ]
    }
    cmd = ["gws","sheets","spreadsheets","values","batchUpdate","--params", json.dumps({"spreadsheetId": sheet_id}), "--json", json.dumps(payload), "--format","json"]
    print("Running:", " ".join(cmd[:3]), "...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout[:3000])
    if result.stderr: print("STDERR:", result.stderr[:2000])
    if result.returncode==0:
        print(f"Synced {len(daily)} daily rows, {len(weekly)} weekly rows, {len(top)} top rows to https://docs.google.com/spreadsheets/d/{sheet_id}/edit")
    else:
        raise SystemExit(result.returncode)

if __name__=="__main__":
    main()
