`/app/shop.db` is a SQLite database (tables: customers, orders, order_items, products). Explore the schema, then answer:

1. Which customer (by `name`) has spent the most in total? (spend = sum of quantity × products.price over their orders)
2. How many orders contain more than one distinct product?
3. What is the name of the product that was never ordered?

Write the three answers to `/app/answers.json` as `{"top_customer": "...", "multi_product_orders": N, "never_ordered": "..."}`.
Also save the SQL you used in `/app/queries.sql`.
