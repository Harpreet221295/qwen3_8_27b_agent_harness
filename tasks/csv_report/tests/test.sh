#!/usr/bin/env bash
# Grader. Writes 1 (pass) or 0 (fail) to /logs/verifier/reward.txt
mkdir -p /logs/verifier; cd /app || exit 1
pass() { echo 1 > /logs/verifier/reward.txt; echo PASS; exit 0; }
fail() { echo 0 > /logs/verifier/reward.txt; echo "FAIL: $1"; exit 0; }
[ -f report.json ] || fail "report.json missing"
[ -f make_report.py ] || fail "make_report.py missing"
python - <<'PY' || fail "content mismatch"
import json,sys
d=json.load(open('/app/report.json'))
exp={"North":37.5,"South":71.5,"East":20.0,"West":20.0}
assert {k:round(v,2) for k,v in d["revenue_by_region"].items()}==exp, d["revenue_by_region"]
assert d["top_product"]=="widget", d["top_product"]
assert d["total_units"]==38, d["total_units"]
assert d["rows_with_missing_units"]==2, d["rows_with_missing_units"]
PY
pass
