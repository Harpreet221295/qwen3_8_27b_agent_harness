`/app/sales.csv` has columns `date,region,product,units,unit_price`. Some rows have messy data:
whitespace around fields, `units` may be blank (treat as 0), and region names differ only by case.

Write `/app/report.json` containing:
```json
{"revenue_by_region": {"<Region title-cased>": <float rounded to 2>, ...},
 "top_product": "<product with highest total units>",
 "total_units": <int>,
 "rows_with_missing_units": <int>}
```
Regions must be title-cased (e.g. "North"). Put the script you used at `/app/make_report.py`.
