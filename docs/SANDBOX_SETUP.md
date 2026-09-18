# Sandbox setup

The agent only ever runs commands inside a sandbox. Three backends:

## 1. Docker via Colima (default, Apple Silicon Mac)
```bash
brew install colima docker
colima start --cpu 4 --memory 8 --disk 40     # a Linux VM with a Docker daemon inside
docker info | head -5                          # should work with no sudo
docker build -t qwen-sandbox:latest -f docker/Dockerfile.sandbox docker/
```
- Each task attempt gets a **fresh container** (`sleep infinity`, 2 CPU, 2 GB RAM, 512 pids, **no network** unless `--network`).
- Files land in `/app`; tests are copied to `/tests` only after the agent finishes (agent cannot read them).
- Container is force-removed at the end; nothing persists.
- A task may ship its own `environment/Dockerfile` (built on top of `qwen-sandbox`) for extra deps.
- Docker Desktop works the same way if you prefer it over Colima. Stop the VM with `colima stop`.
- Clean up stragglers: `docker rm -f $(docker ps -aq --filter label=qwen-harness)`.

Why a container and not a VM: this is what Terminal-Bench and SWE-bench use, images are reproducible, and
`docker` is already the lingua franca of task definitions. Colima itself runs Docker inside a Lima VM, so the
container is one more boundary inside a VM — good enough for a coding-agent eval on your own machine.

## 2. E2B (cloud Firecracker microVMs)
```bash
pip install e2b-code-interpreter
export E2B_API_KEY=...
python run_eval.py --sandbox e2b --parallel 8
```
Use when you want more parallelism than your Mac can host or when Docker is not an option. Each sandbox is a
microVM with its own kernel. Costs money per sandbox-second.

## 3. local (no isolation)
`--sandbox local` runs commands as your user in a temp dir. Use it only to debug the harness (e.g. with
`--oracle`), never with the model driving.

## Adding a task
```
tasks/my_task/
  task.toml            [task] difficulty="medium" tags=["python"] max_steps=30 network=false
  instruction.md       what the agent sees
  environment/         files copied to /app; optional setup.sh (run once, then deleted); optional Dockerfile
  tests/test.sh        must write 1 or 0 to /logs/verifier/reward.txt (partial credit allowed: 0.5)
  solution/solve.sh    reference solution, validated with --oracle
```
Validate: `python run_eval.py --task my_task --oracle` (must pass) and `--noop` (must fail).
