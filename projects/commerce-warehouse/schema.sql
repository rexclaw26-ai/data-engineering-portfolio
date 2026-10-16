-- A simple star schema with customer and product dimensions and an order fact.
CREATE TABLE IF NOT EXISTS dim_customer (
    customer_id TEXT PRIMARY KEY,
    region TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS dim_product (
    product_id TEXT PRIMARY KEY,
    category TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS fact_order (
    order_id TEXT PRIMARY KEY,
    order_date TEXT NOT NULL,
    customer_id TEXT NOT NULL REFERENCES dim_customer(customer_id),
    product_id TEXT NOT NULL REFERENCES dim_product(product_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price_cents INTEGER NOT NULL CHECK (unit_price_cents >= 0),
    revenue_cents INTEGER NOT NULL CHECK (revenue_cents >= 0)
);
