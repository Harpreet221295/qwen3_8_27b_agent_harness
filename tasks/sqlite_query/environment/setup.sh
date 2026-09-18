#!/usr/bin/env bash
cd /app && sqlite3 shop.db <<'SQL'
CREATE TABLE customers(id INTEGER PRIMARY KEY, name TEXT, city TEXT);
CREATE TABLE products(id INTEGER PRIMARY KEY, name TEXT, price REAL);
CREATE TABLE orders(id INTEGER PRIMARY KEY, customer_id INTEGER, ordered_at TEXT);
CREATE TABLE order_items(order_id INTEGER, product_id INTEGER, quantity INTEGER);
INSERT INTO customers VALUES (1,'Asha','Toronto'),(2,'Ben','Ottawa'),(3,'Chen','Montreal'),(4,'Dev','Toronto');
INSERT INTO products VALUES (1,'Keyboard',49.99),(2,'Monitor',199.0),(3,'Mouse',19.5),(4,'Webcam',59.0),(5,'Headset',89.0);
INSERT INTO orders VALUES (1,1,'2026-01-02'),(2,2,'2026-01-03'),(3,1,'2026-01-09'),(4,3,'2026-02-01'),(5,4,'2026-02-11'),(6,2,'2026-02-15');
INSERT INTO order_items VALUES (1,1,1),(1,3,2),(2,2,1),(3,2,1),(3,5,1),(4,3,4),(5,1,1),(6,2,1),(6,3,1),(6,1,1);
SQL
