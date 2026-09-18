#!/usr/bin/env bash
mkdir -p /app/downloads && cd /app/downloads
for f in photo1.jpg Photo2.JPG diagram.png anim.gif report.pdf notes.txt README.md thesis.docx backup.zip data.tar.gz script.py video.mp4 song.MP3; do echo "content of $f" > "$f"; done
: > empty.png; : > empty2.txt
