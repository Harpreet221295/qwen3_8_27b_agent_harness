#!/usr/bin/env bash
cd /app && python - <<'PY'
p='parse_config.py'; s=open(p).read().replace('key, value = line.split("=")','key, value = line.split("=", 1)'); open(p,'w').write(s)
PY
