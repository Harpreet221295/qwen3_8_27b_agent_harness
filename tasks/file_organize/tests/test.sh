#!/usr/bin/env bash
# Grader. Writes 1 (pass) or 0 (fail) to /logs/verifier/reward.txt
mkdir -p /logs/verifier; cd /app || exit 1
pass() { echo 1 > /logs/verifier/reward.txt; echo PASS; exit 0; }
fail() { echo 0 > /logs/verifier/reward.txt; echo "FAIL: $1"; exit 0; }
cd downloads || fail "downloads missing"
chk() { [ -f "$1" ] || fail "$1 not found"; }
for f in images/photo1.jpg images/Photo2.JPG images/diagram.png images/anim.gif docs/report.pdf docs/notes.txt docs/README.md docs/thesis.docx archives/backup.zip archives/data.tar.gz other/script.py other/video.mp4 other/song.MP3; do chk $f; done
[ ! -e empty.png ] && [ ! -e images/empty.png ] && [ ! -e empty2.txt ] && [ ! -e docs/empty2.txt ] || fail "empty files not deleted"
[ "$(find . -maxdepth 1 -type f | grep -vc MANIFEST.txt)" -eq 0 ] || fail "loose files remain: $(find . -maxdepth 1 -type f)"
printf 'archives/backup.zip\narchives/data.tar.gz\ndocs/README.md\ndocs/notes.txt\ndocs/report.pdf\ndocs/thesis.docx\nimages/Photo2.JPG\nimages/anim.gif\nimages/diagram.png\nimages/photo1.jpg\nother/script.py\nother/song.MP3\nother/video.mp4\n' | LC_ALL=C sort > /tmp/exp
LC_ALL=C sort MANIFEST.txt | grep -v '^$' | diff - /tmp/exp >/dev/null || fail "MANIFEST.txt wrong"
pass
