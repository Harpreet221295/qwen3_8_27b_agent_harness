#!/usr/bin/env bash
cd /app
cat > queries.sql <<'SQL'
SELECT c.name, SUM(oi.quantity*p.price) s FROM customers c JOIN orders o ON o.customer_id=c.id JOIN order_items oi ON oi.order_id=o.id JOIN products p ON p.id=oi.product_id GROUP BY c.id ORDER BY s DESC LIMIT 1;
SELECT COUNT(*) FROM (SELECT order_id FROM order_items GROUP BY order_id HAVING COUNT(DISTINCT product_id)>1);
SELECT name FROM products WHERE id NOT IN (SELECT product_id FROM order_items);
SQL
a=$(sqlite3 shop.db "SELECT c.name FROM customers c JOIN orders o ON o.customer_id=c.id JOIN order_items oi ON oi.order_id=o.id JOIN products p ON p.id=oi.product_id GROUP BY c.id ORDER BY SUM(oi.quantity*p.price) DESC LIMIT 1")
b=$(sqlite3 shop.db "SELECT COUNT(*) FROM (SELECT order_id FROM order_items GROUP BY order_id HAVING COUNT(DISTINCT product_id)>1)")
c=$(sqlite3 shop.db "SELECT name FROM products WHERE id NOT IN (SELECT product_id FROM order_items)")
printf '{"top_customer": "%s", "multi_product_orders": %s, "never_ordered": "%s"}\n' "$a" "$b" "$c" > answers.json
