# Data Quality Monitor

A working validation CLI combining SQL-based duplicate checks with Python validations. It audits customer CSV files for duplicate IDs, missing identifiers and emails, email format issues, invalid dates, and invalid/negative balances. Reports are structured JSON.

**Built in this repository:** Not a conceptual project. No third-party packages required.

## Run

```bash
python projects/data-quality/checks.py projects/data-quality/clean_customers.csv
python projects/data-quality/checks.py projects/data-quality/sample_customers.csv --output /tmp/quality-report.json
```

The clean fixture returns `"passed": true` and exit status 0. The intentionally flawed fixture returns `"passed": false` and exit status 1 (expected for a quality gate), with identified duplicate, missing email, invalid email, negative balance, and invalid date.

## Why this matters

A data pipeline should reject or surface bad data instead of silently loading it. The CLI is suited to running as an upstream validation step in a batch workflow. The CSV files contain only fictional sample records.

Tests: `python -m unittest discover -s tests -v`.
