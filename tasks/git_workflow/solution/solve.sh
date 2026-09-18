#!/usr/bin/env bash
set -e; cd /app
echo "notes.tmp" >> .gitignore && git add .gitignore && git commit -qm "Ignore temp files"
git checkout -qb feature/greeting
printf '\n\ndef greet(name):\n    return f"Hello, {name}!"\n' >> app.py
git add app.py && git commit -qm "Add greeting function"
git checkout -q main && git merge -q --ff-only feature/greeting && git tag v0.1.0
