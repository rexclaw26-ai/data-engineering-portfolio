-- One row per UTC date. All money is stored as integer cents.
SELECT event_date,
       COUNT(*) AS event_count,
       COUNT(DISTINCT user_id) AS unique_users,
       SUM(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS purchases,
       ROUND(SUM(revenue_cents) / 100.0, 2) AS revenue_usd
FROM events
GROUP BY event_date
ORDER BY event_date;
