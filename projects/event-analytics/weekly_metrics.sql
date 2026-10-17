-- One row per ISO week (UTC). All money is stored as integer cents; follows same cents logic as daily_metrics.sql.
SELECT strftime('%Y-W%W', event_date) AS week,
       COUNT(*) AS event_count,
       COUNT(DISTINCT user_id) AS unique_users,
       SUM(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS purchases,
       ROUND(SUM(revenue_cents) / 100.0, 2) AS revenue_usd
FROM events
GROUP BY week
ORDER BY week;
