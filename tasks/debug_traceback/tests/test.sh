#!/usr/bin/env bash
# Grader. Writes 1 (pass) or 0 (fail) to /logs/verifier/reward.txt
mkdir -p /logs/verifier; cd /app || exit 1
pass() { echo 1 > /logs/verifier/reward.txt; echo PASS; exit 0; }
fail() { echo 0 > /logs/verifier/reward.txt; echo "FAIL: $1"; exit 0; }
out=$(python parse_config.py configs/prod.ini 2>&1) || fail "prod.ini crashed: $out"
[ "$out" = "$(printf '[server] host=10.0.0.5 port=443 url=https://example.com/path?x=1\n[auth] token= mode=lenient')" ] || fail "prod.ini output wrong:\n$out"
[ "$(python parse_config.py configs/dev.ini 2>&1)" = "[server] host=localhost port=8000" ] || fail "dev.ini wrong"
e=$(python parse_config.py configs/empty.ini 2>&1); c=$?; [ $c = 0 ] && [ -z "$e" ] || fail "empty.ini: exit $c out '$e'"
pass
