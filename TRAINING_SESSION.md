# TRAINING_SESSION — train a small terminal agent on this harness

Instructions for the Claude Code session on the **new MacBook** that runs this project. All paths are relative to the
root of this repo (`qwen3_8_27b_agent_harness/`). Written 2026-10-31.

## Goal (the interview line this must make true)
"I built the harness, then used it as an RL environment: sandboxes on my Mac, model serving and training on RunPod.
I took a 4B model from X% to Y% on held-out terminal tasks it never trained on."

Two questions this answers: *why build your own harness* (it is an environment for models, not an agent for people)
and *have you trained anything on it* (yes, this).

## Architecture
- **Mac (32 GB, 1 TB):** this repo, Docker via Colima, the sandboxes (one container per attempt), the graders,
  all transcripts and results.
- **RunPod (H100):** vLLM serving the model the Mac calls; later the trainer (LoRA SFT, then GRPO).
- The Mac calls RunPod over HTTPS (`QWEN_BASE_URL`, `QWEN_API_KEY`, `QWEN_MODEL` in `.env`, read by
  `harness/config.py`). Never commit `.env` or any key.

## Mode and rules
- Full build, no stubs. Harpreet decides scope and budget; you build, run and report. Ask him only when a decision
  below is marked **ask**.
- **Sole author = Harpreet.** No Claude attribution anywhere: no co-author trailers, no "generated with" lines.
- Commit often with clear messages. Push only when he asks.
- Keep messages to him short and in simple English. One step at a time.
- Gate each phase: do not start the next until the current one's check passes and is logged.
- Changes to the harness itself are welcome (that is part of the story). Keep the existing 12 tasks and the console
  working: rerun `python run_eval.py --oracle` and `--noop` after any harness change.

## Phase 0 — Mac setup (no GPU)
1. Colima with enough room and Intel emulation, since most task images are amd64:
   `colima start --cpu 8 --memory 20 --disk 150 --vm-type vz --vz-rosetta`
2. `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
3. Build the sandbox image (see `docs/SANDBOX_SETUP.md`), then check the graders:
   `python run_eval.py --oracle` (all 12 must pass) and `python run_eval.py --noop` (all 12 must fail).
4. During long runs keep the Mac awake: `caffeinate -dims` in a separate terminal, Mac plugged in.

Check: oracle 12/12 pass, noop 12/12 fail.

## Phase 1 — bring in many varied tasks (no GPU)
Twelve tasks are too few to train on; the model would memorise them. Use public task sets with many different kinds
of jobs:
- **Training pool:** Endless Terminals (arXiv 2601.16443; ~2,500 tasks in Harbor format). Fallbacks: TMAX-15K
  (arXiv 2606.23321), `github.com/Danau5tin/terminal-bench-rl` (331 tasks). Check the license and that the release
  is downloadable before using it; record both in `TRAINING_LOG.md`.
- **Test only, never trained on:** a Terminal-Bench 2.x subset (see `docs/TERMINAL_BENCH.md`) and this repo's own
  `tasks/`.

Work:
1. Write `training/import_tasks.py`: converts the chosen set into this repo's task layout under
   `datasets/<set_name>/<task_id>/` (`instruction.md`, `environment/`, `tests/test.sh`, `solution/solve.sh`,
   `task.toml`). Keep datasets out of git if large (add to `.gitignore`; keep a manifest file in git).
2. Extend the Docker sandbox in `harness/sandbox/` so a task can bring its own image or Dockerfile (the current
   default is one image, `SANDBOX_IMAGE`). Cache built images.
3. Pilot on **20 tasks**: oracle must pass, noop must fail, under amd64 emulation. Note build time, run time and
   failures per task.
4. If the pilot is clean, import about **400**, keep those that pass oracle/noop, and split by task category:
   ~300 train, the rest held out by **whole categories** (so the test measures skills, not memory).
5. Measure how many sandboxes the Mac runs at once without errors (try `--parallel 8`, then 12, 16).

Check: pilot numbers logged; train/held-out manifests committed; safe parallelism found.

## Phase 2 — baseline (first GPU use)
- **Model (ask, default):** Qwen3-4B-Instruct-2507, thinking off. Confirm the exact Hugging Face name exists.
- RunPod H100 PCIe (Community, ~$2/h), vLLM with tool calling on. Server scripts live in the sibling repo
  `qwen3_8_27b_vllm_server` (clone `github.com/Harpreet221295/qwen3_8_27b_vllm_server` next to this repo if it is
  not there) — adapt `serve.sh` for the 4B model.
- From the Mac: held-out set + Terminal-Bench subset + `tasks/`, **3 attempts each**, report pass rate per set.

Check: baseline table in `TRAINING_LOG.md`. Stop the pod when idle.

## Phase 3 — rejection sampling (the guaranteed result)
1. On the ~300 train tasks, 8 attempts each with the base model (or a stronger teacher such as Qwen3.8-27B for
   tasks the 4B never solves; log which is used).
2. Keep only passing transcripts. Convert to chat SFT data with the **same chat and tool-call template** used at
   serving time. Drop duplicates.
3. LoRA SFT on RunPod (pick TRL, ms-swift or LLaMA-Factory; log why). Serve the adapter with vLLM.
4. Re-run the Phase 2 evaluation exactly (same sets, same 3 attempts).
5. Optional round 2: sample again with the new model, retrain (expert iteration).

Check: base vs SFT table on held-out sets, with absolute numbers.

## Phase 4 — GRPO (stretch; only if Phases 0–3 went smoothly)
Harder because the trainer on RunPod needs rollouts from the Mac every step, with token log-probs, and vLLM must
load new weights after every step.
1. Before coding, write `training/GRPO_DESIGN.md`: framework (study `terminal-bench-rl`, veRL agent loop, SkyRL
   remote environments), how the Mac is reached (tunnel, or the Mac pulls jobs from a queue), group size, tasks per
   step, max turns, reward = the task's own `tests/test.sh` score, step-time estimate.
2. Time one full step before budgeting a run. Expect: Mac sandboxes are the bottleneck.
3. Run, then evaluate exactly as in Phase 2.

## Budget and safety
- **Budget cap (ask, default $60 total GPU).** Tell him before going over. Use a `--max-hours` cap or a timed
  shutdown on every pod. Stop pods when idle.
- Sandboxes stay with no network unless a task's grader needs it.

## Logging (required)
- `TRAINING_LOG.md` (repo root): append one entry per event: date · phase · what · issue · fix · numbers · cost.
- Results under `results/training/<phase>/`. Charts as PNG next to the numbers they show.

## Deliverables
- `training/` code, `datasets/*/manifest` files, `TRAINING_LOG.md`.
- New README section **"Training on the harness"**: setup (Mac sandboxes + RunPod), what ran, the base → SFT (→ GRPO)
  table on held-out tasks, one chart, lessons. Absolute numbers next to every gain.
