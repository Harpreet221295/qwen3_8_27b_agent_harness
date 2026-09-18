"""CLI entrypoint. See README for examples."""
import argparse
from harness.runner import run_all
from harness.tasks import load_tasks, TASKS_DIR

ap = argparse.ArgumentParser(description="Evaluate Qwen3.8-27B on agentic coding / terminal tasks")
ap.add_argument("--task", action="append", help="task name (repeatable)")
ap.add_argument("--tag", help="only tasks with this tag")
ap.add_argument("--sandbox", default="docker", choices=["docker", "local", "e2b"])
ap.add_argument("--thinking", default="off", choices=["off", "low", "medium", "xhigh"])
ap.add_argument("--max-steps", type=int, default=30)
ap.add_argument("--max-tokens", type=int, default=4096, help="per model turn (raise for thinking modes)")
ap.add_argument("--repeats", type=int, default=1)
ap.add_argument("--parallel", type=int, default=2)
ap.add_argument("--network", action="store_true", help="allow internet inside the sandbox")
ap.add_argument("--oracle", action="store_true", help="run reference solutions instead of the model")
ap.add_argument("--noop", action="store_true", help="grade untouched tasks (all should fail) to validate graders")
ap.add_argument("--run-id")
ap.add_argument("-v", "--verbose", action="store_true", help="print every tool call")
a = ap.parse_args()

tasks = load_tasks(TASKS_DIR, only=a.task, tag=a.tag)
if not tasks: raise SystemExit("no tasks matched")
if a.thinking != "off" and a.max_tokens < 8192: a.max_tokens = 16384
opts = dict(sandbox=a.sandbox, thinking=a.thinking, max_steps=a.max_steps, max_tokens=a.max_tokens, repeats=a.repeats,
            parallel=a.parallel, network=a.network, oracle=a.oracle, noop=a.noop, run_id=a.run_id, verbose=a.verbose)
run_all(tasks, opts)
