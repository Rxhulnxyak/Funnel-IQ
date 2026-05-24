-- FunnelIQ - E-Commerce Funnel Analysis SQL Queries
-- Target Data Warehouse: Snowflake / BigQuery / Redshift
-- Note: These queries are written in standard ANSI SQL to be adaptable.

-- =====================================================================
-- 1. OVERALL CONVERSION FUNNEL (Session-Based)
-- Calculates the drop-off at each major step of the buying journey.
-- =====================================================================
WITH session_events AS (
    SELECT
        session_id,
        MAX(CASE WHEN event_name = 'page_view' THEN 1 ELSE 0 END) AS has_page_view,
        MAX(CASE WHEN event_name = 'product_view' THEN 1 ELSE 0 END) AS has_product_view,
        MAX(CASE WHEN event_name = 'add_to_cart' THEN 1 ELSE 0 END) AS has_add_to_cart,
        MAX(CASE WHEN event_name = 'begin_checkout' THEN 1 ELSE 0 END) AS has_checkout,
        MAX(CASE WHEN event_name = 'purchase' THEN 1 ELSE 0 END) AS has_purchase
    FROM events
    GROUP BY session_id
)
SELECT
    COUNT(session_id) AS total_sessions,
    SUM(has_page_view) AS sessions_with_page_view,
    SUM(has_product_view) AS sessions_with_product_view,
    SUM(has_add_to_cart) AS sessions_with_add_to_cart,
    SUM(has_checkout) AS sessions_with_checkout,
    SUM(has_purchase) AS sessions_with_purchase,
    -- Conversion rates between steps
    ROUND(SUM(has_product_view) * 100.0 / SUM(has_page_view), 2) AS view_to_product_rate,
    ROUND(SUM(has_add_to_cart) * 100.0 / SUM(has_product_view), 2) AS product_to_cart_rate,
    ROUND(SUM(has_checkout) * 100.0 / SUM(has_add_to_cart), 2) AS cart_to_checkout_rate,
    ROUND(SUM(has_purchase) * 100.0 / SUM(has_checkout), 2) AS checkout_to_purchase_rate,
    -- Overall Conversion Rate
    ROUND(SUM(has_purchase) * 100.0 / COUNT(session_id), 2) AS overall_conversion_rate
FROM session_events;

-- =====================================================================
-- 2. FUNNEL DROP-OFF BY DEVICE TYPE
-- Identifies if specific devices (Mobile vs. Desktop) have worse UX.
-- =====================================================================
WITH session_funnel AS (
    SELECT
        e.session_id,
        s.device_type,
        MAX(CASE WHEN e.event_name = 'product_view' THEN 1 ELSE 0 END) AS view_product,
        MAX(CASE WHEN e.event_name = 'add_to_cart' THEN 1 ELSE 0 END) AS add_cart,
        MAX(CASE WHEN e.event_name = 'begin_checkout' THEN 1 ELSE 0 END) AS checkout,
        MAX(CASE WHEN e.event_name = 'purchase' THEN 1 ELSE 0 END) AS purchase
    FROM events e
    JOIN sessions s ON e.session_id = s.session_id
    GROUP BY e.session_id, s.device_type
)
SELECT
    device_type,
    COUNT(session_id) AS total_sessions,
    SUM(view_product) AS product_views,
    SUM(add_cart) AS cart_adds,
    SUM(checkout) AS checkouts,
    SUM(purchase) AS purchases,
    ROUND(SUM(purchase) * 100.0 / COUNT(session_id), 2) AS cr_percentage,
    ROUND((SUM(checkout) - SUM(purchase)) * 100.0 / NULLIF(SUM(checkout), 0), 2) AS checkout_abandonment_rate
FROM session_funnel
GROUP BY device_type
ORDER BY total_sessions DESC;

-- =====================================================================
-- 3. TIME TO PURCHASE ANALYSIS (Avg Time from First Event to Purchase)
-- =====================================================================
WITH purchase_sessions AS (
    SELECT
        session_id,
        MIN(timestamp) AS session_start_time,
        MAX(CASE WHEN event_name = 'purchase' THEN timestamp END) AS purchase_time
    FROM events
    GROUP BY session_id
    HAVING MAX(CASE WHEN event_name = 'purchase' THEN 1 ELSE 0 END) = 1
)
SELECT
    ROUND(AVG(EXTRACT(EPOCH FROM (purchase_time::timestamp - session_start_time::timestamp)) / 60), 2) AS avg_minutes_to_purchase
FROM purchase_sessions;

-- =====================================================================
-- 4. MOST ABANDONED PRODUCTS (Added to cart, but not purchased)
-- =====================================================================
WITH product_funnel AS (
    SELECT
        product_id,
        category,
        COUNT(DISTINCT CASE WHEN event_name = 'add_to_cart' THEN session_id END) AS added_to_cart_sessions,
        COUNT(DISTINCT CASE WHEN event_name = 'purchase' THEN session_id END) AS purchased_sessions
    FROM events
    WHERE product_id IS NOT NULL
    GROUP BY product_id, category
)
SELECT
    product_id,
    category,
    added_to_cart_sessions,
    purchased_sessions,
    added_to_cart_sessions - purchased_sessions AS abandonments,
    ROUND((added_to_cart_sessions - purchased_sessions) * 100.0 / NULLIF(added_to_cart_sessions, 0), 2) AS abandonment_rate
FROM product_funnel
WHERE added_to_cart_sessions > 50
ORDER BY abandonments DESC
LIMIT 20;

-- =====================================================================
-- 5. TRAFFIC SOURCE ROI (Revenue vs Drop-off by Source)
-- =====================================================================
WITH source_metrics AS (
    SELECT
        s.traffic_source,
        COUNT(DISTINCT s.session_id) as total_sessions,
        COUNT(DISTINCT CASE WHEN e.event_name = 'purchase' THEN s.session_id END) as converting_sessions,
        SUM(o.order_value) as total_revenue
    FROM sessions s
    LEFT JOIN events e ON s.session_id = e.session_id AND e.event_name = 'purchase'
    LEFT JOIN orders o ON s.session_id = o.session_id
    GROUP BY s.traffic_source
)
SELECT
    traffic_source,
    total_sessions,
    converting_sessions,
    ROUND(converting_sessions * 100.0 / total_sessions, 2) AS conversion_rate,
    COALESCE(total_revenue, 0) AS total_revenue,
    ROUND(COALESCE(total_revenue, 0) / NULLIF(total_sessions, 0), 2) AS revenue_per_session
FROM source_metrics
ORDER BY total_revenue DESC;
