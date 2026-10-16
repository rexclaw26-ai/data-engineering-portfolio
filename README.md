# Rexy | SQL & Data Engineering Portfolio

A personal website featuring **real, runnable code** and an accurate summary of my professional background. Source code is public and all sample data is fictional.

## Professional background

I work as a **consultant**, use **SQL frequently** in my work, and use **Python occasionally**. I bring analytical problem-solving and communication skills to technical work while developing my data engineering capabilities. No employers, experience dates, certifications, or work results are claimed without confirmation.

## Completed portfolio projects

| Project | What the code does | Run it |
| --- | --- | --- |
| [Event Analytics ELT](projects/event-analytics/) | Validates CSV events, loads SQLite idempotently, calculates daily users and revenue using SQL | `python projects/event-analytics/pipeline.py --db /tmp/event-demo.sqlite` |
| [Data Quality Monitor](projects/data-quality/) | Audits a dataset with SQL/Python checks and generates JSON quality reports with pass/fail status | `python projects/data-quality/checks.py projects/data-quality/clean_customers.csv` |
| [Commerce Analytics Warehouse](projects/commerce-warehouse/) | Builds a SQL star schema and reports monthly revenue from order-level data | `python projects/commerce-warehouse/build.py --db /tmp/commerce-demo.sqlite` |

Each project has its own README, sample inputs, and source code. They were **built as hands-on portfolio demonstrations**, not previously completed client engagements.

## Run integration tests

From the repository root, with **Python 3.10+**:

```bash
python -m unittest discover -s tests -v
```

Tests are also configured in [GitHub Actions](.github/workflows/tests.yml). All three examples use only the Python standard library and SQLite. You do not need API keys, cloud accounts, or paid tools.

## Website

Open `index.html` in a browser, or view it through GitHub Pages after Pages has published the default branch. The website uses HTML, CSS, and JavaScript with no build process or external dependencies.

## Contact

- GitHub: [rexclaw26-ai](https://github.com/rexclaw26-ai)
- No email or employer details are published because these were not confirmed.

## Development notes

Sample records, dates, and revenue totals are **demonstration data**, not confidential or real employer/customer data. The portfolio will evolve with additional projects and verified work details.
