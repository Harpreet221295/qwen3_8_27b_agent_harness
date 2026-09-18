from __future__ import annotations
import json, sys
from collections import defaultdict
from pathlib import Path


def summarize(records: list[dict], opts: dict | None = None) -> dict:
    by_task = defaultdict(list)
    for r in records: by_task[r["task"]].append(r)
    rows, total_pass, total = [], 0, 0
    for name, rs in sorted(by_task.items()):
        p = sum(1 for r in rs if r["passed"]); n = len(rs); total_pass += p; total += n
        steps = [r["steps"] for r in rs if "steps" in r]
        rows.append({"task": name, "difficulty": rs[0].get("difficulty"), "passed": p, "n": n, "pass_rate": p / n,
                     "avg_steps": sum(steps) / len(steps) if steps else None,
                     "avg_wall_s": sum(r["wall_s"] for r in rs) / n,
                     "avg_completion_tokens": sum(r.get("completion_tokens", 0) for r in rs) / n,
                     "stop_reasons": sorted({str(r.get("stop_reason", r.get("oracle_exit", ""))) for r in rs}),
                     "errors": sum(1 for r in rs if r.get("harness_error"))})
    md = [f"# Results — {opts.get('thinking') if opts else ''} {'(oracle)' if opts and opts.get('oracle') else ''}", "",
          f"**Overall: {total_pass}/{total} = {100 * total_pass / max(1, total):.0f}%**", "",
          "| task | diff | pass | avg steps | avg s | avg gen toks | stop reasons |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['task']} | {r['difficulty']} | {r['passed']}/{r['n']} | {r['avg_steps'] and f'{r['avg_steps']:.1f}' or '-'} | "
                  f"{r['avg_wall_s']:.0f} | {r['avg_completion_tokens']:.0f} | {', '.join(r['stop_reasons'])} |")
    fb = sum(r.get("fallback_parses", 0) for r in records)
    if fb: md.append(f"\n⚠️ {fb} tool calls were parsed from raw text (tool-call parser missed them).")
    return {"overall_pass": total_pass, "overall_n": total, "rows": rows, "markdown": "\n".join(md) + "\n"}


if __name__ == "__main__":
    d = Path(sys.argv[1]); recs = [json.loads(p.read_text()) for p in d.glob("*_r*.json")]
    print(summarize(recs, json.loads((d / "summary.json").read_text()).get("opts") if (d / "summary.json").exists() else None)["markdown"])
