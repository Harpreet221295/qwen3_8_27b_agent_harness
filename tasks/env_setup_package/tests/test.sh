#!/usr/bin/env bash
# Grader. Writes 1 (pass) or 0 (fail) to /logs/verifier/reward.txt
mkdir -p /logs/verifier; cd /app || exit 1
pass() { echo 1 > /logs/verifier/reward.txt; echo PASS; exit 0; }
fail() { echo 0 > /logs/verifier/reward.txt; echo "FAIL: $1"; exit 0; }
python -c "import mathx" 2>/dev/null || fail "mathx not importable"
[ -f output.txt ] || fail "output.txt missing"
[ "$(tr -d '\n' < output.txt)" = "n=6 mean=18.00 std=12.32" ] || fail "output wrong: $(cat output.txt)"
pass
