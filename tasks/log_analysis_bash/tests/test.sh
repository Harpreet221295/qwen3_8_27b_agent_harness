#!/usr/bin/env bash
# Grader. Writes 1 (pass) or 0 (fail) to /logs/verifier/reward.txt
mkdir -p /logs/verifier; cd /app || exit 1
pass() { echo 1 > /logs/verifier/reward.txt; echo PASS; exit 0; }
fail() { echo 0 > /logs/verifier/reward.txt; echo "FAIL: $1"; exit 0; }
for f in top_ips.txt errors.txt summary.txt; do [ -f $f ] || fail "$f missing"; done
diff <(sed 's/[[:space:]]*$//' top_ips.txt | grep -v '^$') /tests/expected_top.txt >/dev/null || fail "top_ips.txt wrong"
diff <(sed 's/[[:space:]]*$//' errors.txt | grep -v '^$') /tests/expected_errors.txt >/dev/null || fail "errors.txt wrong"
diff <(tr -d ' \n' < summary.txt) <(tr -d ' \n' < /tests/expected_summary.txt) >/dev/null || fail "summary.txt wrong: $(cat summary.txt)"
pass
