import os, re

# ---- strings ----
def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

def titlecase(s):
    return " ".join(w.capitalize() for w in s.split())

# ---- maths ----
def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0

# ---- files ----
def read_lines(path):
    with open(path) as f:
        return [l.rstrip("\n") for l in f]

def file_size(path):
    return os.path.getsize(path)
