#!/usr/bin/env bash
# Grader. Writes 1 (pass) or 0 (fail) to /logs/verifier/reward.txt
mkdir -p /logs/verifier; cd /app || exit 1
pass() { echo 1 > /logs/verifier/reward.txt; echo PASS; exit 0; }
fail() { echo 0 > /logs/verifier/reward.txt; echo "FAIL: $1"; exit 0; }
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || fail "not a git repo"
[ -z "$(git status --porcelain)" ] || fail "working tree not clean: $(git status --porcelain | head -3)"
git log --format=%s main | grep -qx "Ignore temp files" || fail "no 'Ignore temp files' commit on main"
git log --format=%s main | grep -qx "Add greeting function" || fail "greeting commit not on main"
git rev-parse --verify feature/greeting >/dev/null 2>&1 || fail "feature/greeting branch missing"
git check-ignore -q notes.tmp || fail "notes.tmp not ignored"
git ls-files --error-unmatch notes.tmp >/dev/null 2>&1 && fail "notes.tmp is tracked"
[ "$(git rev-parse v0.1.0^{commit} 2>/dev/null)" = "$(git rev-parse main)" ] || fail "tag v0.1.0 not on main head"
python -c "from app import greet, add; assert greet('Harpreet')=='Hello, Harpreet!'; assert add(1,2)==3" || fail "greet() wrong"
pass
