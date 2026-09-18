#!/usr/bin/env bash
# Grader. Writes 1 (pass) or 0 (fail) to /logs/verifier/reward.txt
mkdir -p /logs/verifier; cd /app || exit 1
pass() { echo 1 > /logs/verifier/reward.txt; echo PASS; exit 0; }
fail() { echo 0 > /logs/verifier/reward.txt; echo "FAIL: $1"; exit 0; }
[ -f answers.json ] || fail "answers.json missing"; [ -f queries.sql ] || fail "queries.sql missing"
python - <<'PY' || fail "wrong answers: $(cat /app/answers.json)"
import json; d=json.load(open('/app/answers.json'))
assert d["top_customer"]=="Ben", d
assert int(d["multi_product_orders"])==3, d
assert d["never_ordered"]=="Webcam", d
PY
pass
