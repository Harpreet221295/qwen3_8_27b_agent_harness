#!/usr/bin/env bash
# Grader. Writes 1 (pass) or 0 (fail) to /logs/verifier/reward.txt
mkdir -p /logs/verifier; cd /app || exit 1
pass() { echo 1 > /logs/verifier/reward.txt; echo PASS; exit 0; }
fail() { echo 0 > /logs/verifier/reward.txt; echo "FAIL: $1"; exit 0; }
cmp -s /tests/test_inventory.py /app/test_inventory.py || fail "tests were modified"
python -m pytest -q /app/test_inventory.py -p no:cacheprovider > /logs/verifier/pytest.log 2>&1 && pass || fail "pytest failed: $(tail -5 /logs/verifier/pytest.log)"
