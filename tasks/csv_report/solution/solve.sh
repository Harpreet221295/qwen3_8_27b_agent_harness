#!/usr/bin/env bash
cat > /app/make_report.py <<'PY'
import csv, json
from collections import defaultdict
rev=defaultdict(float); units=defaultdict(int); total=0; missing=0
for r in csv.DictReader(open('/app/sales.csv')):
    r={k.strip():(v or '').strip() for k,v in r.items()}
    u=int(r['units']) if r['units'] else 0
    if not r['units']: missing+=1
    reg=r['region'].title(); rev[reg]+=u*float(r['unit_price']); units[r['product']]+=u; total+=u
json.dump({"revenue_by_region":{k:round(v,2) for k,v in rev.items()},"top_product":max(units,key=units.get),
           "total_units":total,"rows_with_missing_units":missing},open('/app/report.json','w'),indent=1)
PY
cd /app && python make_report.py
