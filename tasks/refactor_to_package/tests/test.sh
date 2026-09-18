#!/usr/bin/env bash
# Grader. Writes 1 (pass) or 0 (fail) to /logs/verifier/reward.txt
mkdir -p /logs/verifier; cd /app || exit 1
pass() { echo 1 > /logs/verifier/reward.txt; echo PASS; exit 0; }
fail() { echo 0 > /logs/verifier/reward.txt; echo "FAIL: $1"; exit 0; }
[ ! -f monolith.py ] || fail "monolith.py still exists"
for f in utils/__init__.py utils/strings.py utils/maths.py utils/files.py; do [ -f $f ] || fail "$f missing"; done
diff <(grep -v '^from utils import \*' test_monolith.py) <(grep -v '^from monolith import \*' /tests/test_monolith.py) >/dev/null || fail "test file changed beyond the import line"
grep -q '^from utils import \*' test_monolith.py || fail "import line not updated"
python -c "from utils import slugify, titlecase, clamp, mean, read_lines, file_size; from utils.strings import slugify; from utils.maths import clamp; from utils.files import read_lines" || fail "imports broken"
python -m pytest -q test_monolith.py -p no:cacheprovider >/logs/verifier/pytest.log 2>&1 || fail "pytest failed"
pass
