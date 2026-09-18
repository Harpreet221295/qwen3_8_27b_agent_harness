#!/usr/bin/env bash
# Grader. Writes 1 (pass) or 0 (fail) to /logs/verifier/reward.txt
mkdir -p /logs/verifier; cd /app || exit 1
pass() { echo 1 > /logs/verifier/reward.txt; echo PASS; exit 0; }
fail() { echo 0 > /logs/verifier/reward.txt; echo "FAIL: $1"; exit 0; }
cmp -s client_check.py /tests/client_check.py || fail "client_check.py modified"
pkill -f "python /app/server.py" 2>/dev/null; sleep 1
python /app/server.py >/logs/verifier/server.log 2>&1 & SP=$!
sleep 2
out=$(timeout 60 python client_check.py 2>&1); code=$?
kill $SP 2>/dev/null
[ $code = 0 ] && echo "$out" | grep -q "ALL OK" && pass || fail "$out"
