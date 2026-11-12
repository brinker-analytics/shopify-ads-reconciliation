-- Reconciliation in SQL (BigQuery syntax). Replace `project.dataset.orders`
-- with a table that has the columns in template/orders_template.csv:
-- one row per Shopify order.

-- 0. Each order must appear once. Expect zero rows.
SELECT order_id, COUNT(*) AS n
FROM `project.dataset.orders`
GROUP BY order_id
HAVING n > 1;

-- 1. What each platform claims, next to the store total. Claims overlap.
WITH totals AS (
  SELECT COUNT(*) AS store_orders, SUM(net_sales) AS store_sales
  FROM `project.dataset.orders`
)
SELECT row_name, orders, net_sales, SAFE_DIVIDE(orders, store_orders) AS share_of_store_orders
FROM (
  SELECT 'Meta (click)' AS row_name, COUNTIF(meta_claim = 'click') AS orders,
         SUM(IF(meta_claim = 'click', net_sales, 0)) AS net_sales, 1 AS sort_key
  FROM `project.dataset.orders`
  UNION ALL
  SELECT 'Meta (view)', COUNTIF(meta_claim = 'view'), SUM(IF(meta_claim = 'view', net_sales, 0)), 2
  FROM `project.dataset.orders`
  UNION ALL
  SELECT 'Google Ads', COUNTIF(IFNULL(google_claim, '') != ''),
         SUM(IF(IFNULL(google_claim, '') != '', net_sales, 0)), 3
  FROM `project.dataset.orders`
  UNION ALL
  SELECT 'Shopify orders (store total)', COUNT(*), SUM(net_sales), 9
  FROM `project.dataset.orders`
), totals
ORDER BY sort_key;

-- 2. MTA, one row per order, with an Unattributed row. Adds to the store total.
SELECT
  IF(IFNULL(mta_channel, '') = '', 'Unattributed', mta_channel) AS row_name,
  COUNT(*) AS orders,
  SUM(net_sales) AS net_sales
FROM `project.dataset.orders`
GROUP BY row_name
ORDER BY row_name = 'Unattributed', orders DESC;

-- 3. GA4, one row per order, with a Not in GA4 row. Adds to the store total.
SELECT
  IF(IFNULL(ga4_channel, '') = '', 'Not in GA4', ga4_channel) AS row_name,
  COUNT(*) AS orders,
  SUM(net_sales) AS net_sales
FROM `project.dataset.orders`
GROUP BY row_name
ORDER BY row_name = 'Not in GA4', orders DESC;
