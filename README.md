# qwen3_8_27b_agent_harness — agentic coding + terminal-use eval for Qwen3.8-27B

Runs on your Mac. The model runs on RunPod (see `qwen3_8_27b_vllm_server`). Each task is executed by
the model inside an isolated **sandbox** (Docker container by default), then graded by a test
script inside that same sandbox. Nothing the model runs touches your Mac.

```
   Mac                                   RunPod
 ┌──────────────────────────┐          ┌────────────────────┐
 │ run_eval.py              │  HTTPS   │ vLLM               │
 │  └─ agent loop  ─────────┼─────────▶│ Qwen3.8-27B        │
 │       │ tool calls       │◀─────────┤ (tool-call parser) │
 │       ▼                  │          └────────────────────┘
 │  Docker sandbox (Colima) │
 │   /app  ← task files     │
 │   bash / read / write    │
 │   tests/test.sh → reward │
 └──────────────────────────┘
```

## Setup (one time)
```bash
# 1. container runtime (Apple Silicon)
brew install colima docker
colima start --cpu 4 --memory 8 --disk 40

# 2. python env
cd qwen3_8_27b_agent_harness
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # QWEN_BASE_URL, QWEN_API_KEY

# 3. sandbox image
docker build -t qwen-sandbox:latest -f docker/Dockerfile.sandbox docker/
```

## Run
```bash
python run_eval.py --oracle                 # sanity: run reference solutions, all tasks must pass
python run_eval.py                          # model on all tasks, thinking off
python run_eval.py --task fix_failing_test  # one task
python run_eval.py --thinking low --repeats 3 --parallel 3   # pass@k style
python run_eval.py --sandbox local          # NO isolation, dev only
python -m harness.report results/<run_id>  # re-print a summary
```

Results: `results/<run_id>/` → one JSON transcript per task attempt + `summary.md` + `summary.json`.

## Task format (Harbor / Terminal-Bench style)
```
tasks/<name>/
  task.toml          # difficulty, tags, timeouts, max_steps
  instruction.md     # what the agent is told
  environment/       # files copied to /app  (optional Dockerfile → custom image)
  tests/test.sh      # grader; writes 0 or 1 to /logs/verifier/reward.txt
  solution/solve.sh  # reference solution used by --oracle
```
Add a task: copy a folder, edit the four files, run `python run_eval.py --oracle --task <name>`.

## Tools the agent gets
`bash` (cwd persists across calls), `read_file`, `write_file`, `edit_file` (exact string
replace), `finish`. Output is truncated to keep context bounded. See `harness/tools.py`.

## Sandboxes
| backend | isolation | when |
|---|---|---|
| `docker` (default) | container via Colima/Docker Desktop, CPU/mem limits, optional no-network | local eval |
| `e2b` | Firecracker microVM in the cloud (`pip install e2b-code-interpreter`, `E2B_API_KEY`) | no Docker, or parallel at scale |
| `local` | none (temp dir subprocess) | debugging the harness only |

More in `docs/SANDBOX_SETUP.md`. To run the official Terminal-Bench 2 against the endpoint see
`docs/TERMINAL_BENCH.md`.

## Knobs (run_eval.py)
`--thinking off|low|medium|xhigh`, `--max-steps`, `--max-tokens`, `--repeats`, `--parallel`,
`--network` (allow internet in sandbox), `--tag` (filter tasks), `--sandbox`.
