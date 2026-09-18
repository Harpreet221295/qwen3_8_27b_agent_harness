#!/usr/bin/env bash
cd /app && python - <<'PY'
p='server.py'; s=open(p).read()
s=s.replace('"Content-Type", "text/plain"','"Content-Type", "application/json"')
s=s.replace('return self._send(200, TODOS.values())','return self._send(200, list(TODOS.values()))')
s=s.replace('        if title is None:\n','        if not title:\n')
s=s.replace('        TODOS[NEXT_ID] = todo\n        self._send(200, todo)','        TODOS[NEXT_ID] = todo\n        NEXT_ID += 1\n        self._send(201, todo)')
s=s.replace('        self._send(204, {})','        self._send(204)')
s=s.replace('            return int(parts[1])','            return int(parts[1]) if parts[1].isdigit() else None')
open(p,'w').write(s)
PY
