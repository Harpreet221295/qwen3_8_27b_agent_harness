#!/usr/bin/env bash
cd /app
python - <<'PY'
p='inventory.py'; s=open(p).read()
s=s.replace('self.items[name]["qty"] = qty','self.items[name]["qty"] += qty')
s=s.replace('item["qty"] + item["price"]','item["qty"] * item["price"]')
s=s.replace('it["qty"] > threshold','it["qty"] < threshold')
open(p,'w').write(s)
PY
