#!/usr/bin/env bash
# Grader. Writes 1 (pass) or 0 (fail) to /logs/verifier/reward.txt
mkdir -p /logs/verifier; cd /app || exit 1
pass() { echo 1 > /logs/verifier/reward.txt; echo PASS; exit 0; }
fail() { echo 0 > /logs/verifier/reward.txt; echo "FAIL: $1"; exit 0; }
make clean >/dev/null 2>&1; make >/logs/verifier/make.log 2>&1 || fail "make failed: $(tail -3 /logs/verifier/make.log)"
[ -x calc ] || fail "calc not built"
[ "$(./calc 6 7)" = "42" ] || fail "6*7"
[ "$(./calc -d 10 4)" = "2.5" ] || fail "10/4 got $(./calc -d 10 4)"
err=$(./calc -d 10 0 2>&1 >/dev/null); code=$?
[ "$code" = "2" ] || fail "div-by-zero exit code $code"
echo "$err" | grep -q "division by zero" || fail "div-by-zero message: '$err'"
make clean >/dev/null 2>&1; [ ! -f calc ] && [ ! -f main.o ] || fail "make clean incomplete"
pass
