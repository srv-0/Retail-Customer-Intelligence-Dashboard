-- ============================================================
-- RETAIL CUSTOMER INTELLIGENCE — SQL QUERIES
-- Database: retail_analytics.db
-- ============================================================

-- Q1: Total revenue, orders and customers overview
SELECT
    COUNT(DISTINCT order_id)   AS total_orders,
    COUNT(DISTINCT customer_id) AS total_customers,
    ROUND(SUM(total_amount),0) AS total_revenue_inr,
    ROUND(AVG(total_amount),0) AS avg_order_value
FROM transactions;

-- Q2: Monthly revenue trend
SELECT
    SUBSTR(order_date,1,7)     AS month,
    COUNT(DISTINCT order_id)   AS orders,
    ROUND(SUM(total_amount),0) AS revenue
FROM transactions
GROUP BY month
ORDER BY month;

-- Q3: Revenue and orders by category
SELECT
    category,
    COUNT(DISTINCT order_id)        AS total_orders,
    ROUND(SUM(total_amount),0)      AS total_revenue,
    ROUND(AVG(total_amount),0)      AS avg_order_value,
    ROUND(AVG(rating),2)            AS avg_rating,
    SUM(returned)                   AS returns
FROM transactions
GROUP BY category
ORDER BY total_revenue DESC;

-- Q4: Top 10 customers by lifetime value
SELECT
    customer_id,
    city,
    total_orders,
    ROUND(total_spent,0)            AS lifetime_value_inr,
    avg_order_value,
    avg_rating
FROM customers
ORDER BY total_spent DESC
LIMIT 10;

-- Q5: City-wise performance
SELECT
    city,
    COUNT(DISTINCT customer_id)    AS customers,
    COUNT(DISTINCT order_id)       AS orders,
    ROUND(SUM(total_amount),0)     AS revenue,
    ROUND(AVG(total_amount),0)     AS avg_order_value
FROM transactions
GROUP BY city
ORDER BY revenue DESC;

-- Q6: Payment method preference
SELECT
    payment_method,
    COUNT(*)                        AS transactions,
    ROUND(COUNT(*)*100.0/(SELECT COUNT(*) FROM transactions),1) AS pct
FROM transactions
GROUP BY payment_method
ORDER BY transactions DESC;

-- Q7: Return rate by category
SELECT
    category,
    COUNT(*)                        AS total_orders,
    SUM(returned)                   AS returns,
    ROUND(SUM(returned)*100.0/COUNT(*),1) AS return_rate_pct
FROM transactions
GROUP BY category
ORDER BY return_rate_pct DESC;

-- Q8: Customers at churn risk (no purchase in last 90 days of dataset)
SELECT
    customer_id,
    MAX(order_date)                AS last_purchase,
    JULIANDAY('2024-12-31') - JULIANDAY(MAX(order_date)) AS days_since_purchase,
    COUNT(DISTINCT order_id)       AS total_orders,
    ROUND(SUM(total_amount),0)     AS lifetime_value
FROM transactions
GROUP BY customer_id
HAVING days_since_purchase > 90
ORDER BY lifetime_value DESC
LIMIT 20;

-- Q9: Peak shopping day of week
SELECT
    CASE CAST(strftime('%w', order_date) AS INTEGER)
        WHEN 0 THEN 'Sunday'    WHEN 1 THEN 'Monday'
        WHEN 2 THEN 'Tuesday'   WHEN 3 THEN 'Wednesday'
        WHEN 4 THEN 'Thursday'  WHEN 5 THEN 'Friday'
        ELSE 'Saturday' END     AS day_of_week,
    COUNT(*)                    AS transactions,
    ROUND(SUM(total_amount),0)  AS revenue
FROM transactions
GROUP BY day_of_week
ORDER BY transactions DESC;

-- Q10: High value customers who haven't bought in 60+ days (priority retention list)
SELECT
    c.customer_id,
    c.city,
    c.total_orders,
    ROUND(c.total_spent,0)          AS lifetime_value,
    c.last_order,
    JULIANDAY('2024-12-31') - JULIANDAY(c.last_order) AS days_inactive
FROM customers c
WHERE c.total_spent > (SELECT AVG(total_spent) FROM customers)
  AND JULIANDAY('2024-12-31') - JULIANDAY(c.last_order) > 60
ORDER BY c.total_spent DESC
LIMIT 15;
