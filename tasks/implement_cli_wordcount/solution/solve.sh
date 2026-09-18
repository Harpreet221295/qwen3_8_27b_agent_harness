#!/usr/bin/env bash
cat > /app/wc.py <<'PY'
import sys
def count(path):
    data = open(path, encoding="utf-8").read()
    return data.count("\n"), len(data.split()), len(data)
def main(argv):
    flags = [a for a in argv if a.startswith("-")]; files = [a for a in argv if not a.startswith("-")]
    show = [f in flags for f in ("-l", "-w", "-c")]
    if not any(show): show = [True, True, True]
    tot = [0, 0, 0]; rc = 0
    for f in files:
        try: c = count(f)
        except OSError:
            print(f"wc.py: {f}: No such file", file=sys.stderr); rc = 1; continue
        tot = [t + x for t, x in zip(tot, c)]
        print(" ".join(str(v) for v, s in zip(c, show) if s), f)
    if len(files) > 1: print(" ".join(str(v) for v, s in zip(tot, show) if s), "total")
    return rc
if __name__ == "__main__": sys.exit(main(sys.argv[1:]))
PY
