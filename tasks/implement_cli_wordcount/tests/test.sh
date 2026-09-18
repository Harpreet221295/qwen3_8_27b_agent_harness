#!/usr/bin/env bash
# Grader. Writes 1 (pass) or 0 (fail) to /logs/verifier/reward.txt
mkdir -p /logs/verifier; cd /app || exit 1
pass() { echo 1 > /logs/verifier/reward.txt; echo PASS; exit 0; }
fail() { echo 0 > /logs/verifier/reward.txt; echo "FAIL: $1"; exit 0; }
[ -f wc.py ] || fail "wc.py missing"
run() { python wc.py "$@" 2>/dev/null; }
[ "$(run samples/a.txt)" = "4 6 35 samples/a.txt" ] || fail "basic: got '$(run samples/a.txt)'"
[ "$(run -l samples/a.txt)" = "4 samples/a.txt" ] || fail "-l"
[ "$(run -w -c samples/b.txt)" = "5 24 samples/b.txt" ] || fail "-w -c: got '$(run -w -c samples/b.txt)'"
[ "$(run samples/a.txt samples/b.txt | tail -1)" = "5 11 59 total" ] || fail "total: got '$(run samples/a.txt samples/b.txt | tail -1)'"
python wc.py samples/a.txt nope.txt >/dev/null 2>/tmp/err; code=$?
[ "$code" = "1" ] || fail "exit code for missing file was $code"
grep -q "No such file" /tmp/err || fail "missing-file stderr"
pass
