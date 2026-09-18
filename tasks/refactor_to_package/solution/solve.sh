#!/usr/bin/env bash
cd /app && mkdir -p utils
cat > utils/strings.py <<'PY'
import re
def slugify(s): return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
def titlecase(s): return " ".join(w.capitalize() for w in s.split())
PY
cat > utils/maths.py <<'PY'
def clamp(x, lo, hi): return max(lo, min(hi, x))
def mean(xs): return sum(xs) / len(xs) if xs else 0.0
PY
cat > utils/files.py <<'PY'
import os
def read_lines(path):
    with open(path) as f: return [l.rstrip("\n") for l in f]
def file_size(path): return os.path.getsize(path)
PY
cat > utils/__init__.py <<'PY'
from .strings import slugify, titlecase
from .maths import clamp, mean
from .files import read_lines, file_size
__all__ = ["slugify", "titlecase", "clamp", "mean", "read_lines", "file_size"]
PY
python -c "p='test_monolith.py'; s=open(p).read().replace('from monolith import *','from utils import *'); open(p,'w').write(s)" && rm monolith.py
