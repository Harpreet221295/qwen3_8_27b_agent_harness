"""Run tasks: sandbox up -> files in -> agent (or oracle) -> tests -> reward -> record."""
from __future__ import annotations
import json, time, traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from rich.console import Console
from . import config
from .agent import Agent
from .sandbox import make_sandbox
from .tasks import Task
from .tools import ToolExecutor

console = Console()
RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"


def run_one(task: Task, opts: dict, rep: int) -> dict:
    rec = {"task": task.name, "rep": rep, "difficulty": task.difficulty, "tags": task.tags, "mode": "noop" if opts.get("noop") else ("oracle" if opts["oracle"] else "agent"),
           "thinking": opts["thinking"], "model": config.MODEL, "reward": 0.0, "passed": False, "started": datetime.now().isoformat()}
    t0 = time.time()
    sb_kw = {"image": config.SANDBOX_IMAGE, "network": opts["network"] or task.network,
             "dockerfile_dir": task.env_dir if (task.env_dir / "Dockerfile").exists() else None}
    try:
        with make_sandbox(opts["sandbox"], **sb_kw) as sb:
            if task.env_dir.exists(): sb.upload_dir(task.env_dir, "/app")
            if (task.env_dir / "setup.sh").exists():
                r = sb.exec("bash /app/setup.sh && rm -f /app/setup.sh", timeout=300); rec["setup_exit"] = r.exit_code
            if opts.get("noop"):
                pass  # baseline: grade the untouched task; every grader should fail
            elif opts["oracle"]:
                sb.write_file("/tests/solve.sh", task.solution.read_text())
                r = sb.exec("bash /tests/solve.sh", timeout=task.agent_timeout_s, cwd="/app")
                rec["oracle_exit"] = r.exit_code; rec["oracle_output"] = r.output[-2000:]
            else:
                agent = Agent(ToolExecutor(sb), thinking=opts["thinking"], max_steps=min(task.max_steps, opts["max_steps"]),
                              max_tokens=opts["max_tokens"], verbose=opts["verbose"])
                res = agent.run(task.instruction)
                rec.update({k: v for k, v in asdict(res).items() if k != "transcript"}); rec["transcript"] = res.transcript
            # grade
            sb.upload_dir(task.tests_dir, "/tests")
            sb.exec("rm -f /logs/verifier/reward.txt", timeout=10)
            r = sb.exec("bash /tests/test.sh", timeout=task.test_timeout_s, cwd="/app")
            rec["test_exit"] = r.exit_code; rec["test_output"] = r.output[-3000:]
            try: rec["reward"] = float(sb.read_file("/logs/verifier/reward.txt").strip().splitlines()[0])
            except Exception: rec["reward"] = 0.0
            rec["passed"] = rec["reward"] >= 1.0
    except Exception as e:
        rec["harness_error"] = f"{type(e).__name__}: {e}"; rec["trace"] = traceback.format_exc()[-1500:]
    rec["wall_s"] = round(time.time() - t0, 1)
    return rec


def run_all(tasks: list[Task], opts: dict) -> Path:
    run_id = opts.get("run_id") or datetime.now().strftime("%Y%m%d_%H%M%S") + ("_noop" if opts.get("noop") else "_oracle" if opts["oracle"] else f"_{opts['thinking']}")
    out = RESULTS_DIR / run_id; out.mkdir(parents=True, exist_ok=True)
    jobs = [(t, rep) for t in tasks for rep in range(opts["repeats"])]
    console.print(f"[bold]run {run_id}[/]: {len(tasks)} tasks × {opts['repeats']} reps, sandbox={opts['sandbox']}, parallel={opts['parallel']}")
    records = []
    with ThreadPoolExecutor(max_workers=opts["parallel"]) as pool:
        futs = {pool.submit(run_one, t, opts, rep): (t, rep) for t, rep in jobs}
        for f in as_completed(futs):
            rec = f.result(); records.append(rec)
            (out / f"{rec['task']}_r{rec['rep']}.json").write_text(json.dumps(rec, indent=1, default=str))
            mark = "✅" if rec["passed"] else "❌"
            extra = rec.get("harness_error") or f"steps={rec.get('steps', '-')} stop={rec.get('stop_reason', rec.get('oracle_exit', '-'))}"
            console.print(f"{mark} {rec['task']} r{rec['rep']}  reward={rec['reward']}  {rec['wall_s']}s  {extra}")
    write_summary(out, records, opts)
    return out


def write_summary(out: Path, records: list[dict], opts: dict):
    from .report import summarize
    summary = summarize(records, opts)
    (out / "summary.json").write_text(json.dumps(summary, indent=1))
    (out / "summary.md").write_text(summary["markdown"])
    console.print(summary["markdown"])
