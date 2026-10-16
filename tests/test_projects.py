"""Integration tests for the three runnable portfolio projects."""
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def run_script(*args):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True)

class EventPipelineTests(unittest.TestCase):
    def test_load_reports_and_idempotency(self):
        with tempfile.TemporaryDirectory() as folder:
            db_path = Path(folder) / "events.sqlite"
            script = ROOT / "projects" / "event-analytics" / "pipeline.py"
            first = run_script(script, "--db", db_path)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertIn("'inserted': 7", first.stdout)
            self.assertIn("'duplicates': 1", first.stdout)
            self.assertIn("'rejected': 1", first.stdout)
            with sqlite3.connect(db_path) as conn:
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM events").fetchone()[0], 7)
                self.assertEqual(conn.execute("SELECT SUM(revenue_cents) FROM events").fetchone()[0], 8449)
                self.assertEqual(conn.execute("SELECT COUNT(DISTINCT event_date) FROM events").fetchone()[0], 2)
            second = run_script(script, "--db", db_path)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertIn("'inserted': 0", second.stdout)

class DataQualityTests(unittest.TestCase):
    def test_clean_fixture_passes(self):
        script = ROOT / "projects" / "data-quality" / "checks.py"
        fixture = ROOT / "projects" / "data-quality" / "clean_customers.csv"
        result = run_script(script, fixture)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report["passed"])
        self.assertEqual(report["rows_checked"], 3)

    def test_dirty_fixture_fails_with_explanations(self):
        script = ROOT / "projects" / "data-quality" / "checks.py"
        fixture = ROOT / "projects" / "data-quality" / "sample_customers.csv"
        result = run_script(script, fixture)
        self.assertEqual(result.returncode, 1, result.stderr)
        report = json.loads(result.stdout)
        self.assertFalse(report["passed"])
        failed = {rule["rule"] for rule in report["checks"] if rule["failures"] > 0}
        self.assertEqual(failed, {
            "duplicate_customer_ids", "missing_emails", "invalid_email_format",
            "invalid_signup_dates", "invalid_or_negative_balances"
        })

class CommerceWarehouseTests(unittest.TestCase):
    def test_star_schema_revenue_and_idempotency(self):
        with tempfile.TemporaryDirectory() as folder:
            db_path = Path(folder) / "commerce.sqlite"
            script = ROOT / "projects" / "commerce-warehouse" / "build.py"
            first = run_script(script, "--db", db_path)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertIn("'inserted': 6", first.stdout)
            with sqlite3.connect(db_path) as conn:
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM fact_order").fetchone()[0], 6)
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM dim_customer").fetchone()[0], 3)
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM dim_product").fetchone()[0], 3)
                self.assertEqual(conn.execute("SELECT SUM(revenue_cents) FROM fact_order").fetchone()[0], 27346)
                monthly = conn.execute(
                    "SELECT substr(order_date, 1, 7), SUM(revenue_cents) "
                    "FROM fact_order GROUP BY 1 ORDER BY 1"
                ).fetchall()
                self.assertEqual(monthly, [("2026-08", 10947), ("2026-09", 16399)])
            second = run_script(script, "--db", db_path)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertIn("'inserted': 0", second.stdout)

if __name__ == "__main__":
    unittest.main()
