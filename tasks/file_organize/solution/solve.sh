#!/usr/bin/env bash
cd /app/downloads && mkdir -p images docs archives other && : > MANIFEST.txt
for f in *; do
  [ -f "$f" ] || continue; [ "$f" = MANIFEST.txt ] && continue
  if [ ! -s "$f" ]; then rm -f "$f"; continue; fi
  l=$(echo "$f" | tr 'A-Z' 'a-z')
  case "$l" in *.jpg|*.jpeg|*.png|*.gif) d=images;; *.pdf|*.docx|*.txt|*.md) d=docs;; *.zip|*.tar.gz) d=archives;; *) d=other;; esac
  mv "$f" "$d/" && echo "$d/$f" >> MANIFEST.txt
done
LC_ALL=C sort -o MANIFEST.txt MANIFEST.txt
