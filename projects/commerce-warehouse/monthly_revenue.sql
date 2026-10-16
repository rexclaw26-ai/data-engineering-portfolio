-- Revenue by calendar month and product category; no floating point money storage.
SELECT substr(f.order_date, 1, 7) AS month,
       p.category,
       COUNT(DISTINCT f.order_id) AS orders,
       ROUND(SUM(f.revenue_cents) / 100.0, 2) AS revenue_usd
FROM fact_order AS f
JOIN dim_product AS p ON p.product_id = f.product_id
GROUP BY substr(f.order_date, 1, 7), p.category
ORDER BY month, p.category;
