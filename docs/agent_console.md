# Agent console (port 7861)

Start: `.venv/bin/python -m uvicorn ui.app:app --port 7861` (or `../start_uis.sh`). Backend `ui/app.py`, page `ui/static/index.html`.
The agent loop is `harness/agent.py`; tools in `harness/tools.py`; sandboxes in `harness/sandbox/`.

## Tabs
- **Run**: one task in a fresh sandbox. Pick a task (its files are loaded, its grader runs) or type a custom instruction in
  the bottom bar (task files still loaded if a task is selected, but no grader). Thinking, sandbox, max steps, tokens, internet.
- **Session**: a persistent sandbox you chat with. Files and conversation persist across messages. Plain questions get a
  text reply (chat mode); work requests get tool use; `finish` marks a completed piece of work. Sessions list on the left,
  ✕ deletes the sandbox but keeps the transcript (`results/sessions/`). Each live session holds a 2 GB container.
- **Past runs**: every batch run from `run_eval.py` with full transcripts.

## What you see live
Per step: the gold thinking panel (glows while streaming), the model's text, tool calls in blue with arguments typing out
as the model writes them (file contents, commands), the tool output, then a check mark with the tool's duration. A status
row under the current step shows the phase (thinking / writing file / running bash…), elapsed time and a token estimate.
Step headers collapse; "collapse finished steps automatically" is in the Run sidebar.

## Safety model
Everything the model runs happens in a Docker container (Colima on the Mac): 2 CPU, 2 GB RAM, 512 pids, no network unless
you tick "allow internet" (then Docker's bridge network → your Wi-Fi; still no access to Mac files). The container is
deleted at the end of a run or when a session is closed. "local" sandbox = no isolation, guarded by a confirmation dialog:
only for debugging the harness itself.

## Grading
A task's `tests/test.sh` runs inside the same container after the agent finishes and writes `/logs/verifier/reward.txt`
(0/1). Validate a new task with `python run_eval.py --task <name> --oracle` (reference solution must pass) and `--noop`
(untouched task must fail). Format mirrors Harbor / Terminal-Bench (`docs/TERMINAL_BENCH.md`).

## Tool schema slip to watch
Occasionally the model calls `write_file` with a `command` field instead of `content`; the tool rejects it and the model
retries correctly. Count these in transcripts (`error: bad arguments`) when comparing models or thinking modes.

## Related
- `docs/SANDBOX_SETUP.md`: Colima / E2B / local, adding tasks.
- `docs/TERMINAL_BENCH.md`: running the official Terminal-Bench 2 via Harbor against the pod.
- `RESULTS.md`: first batch (12/12, thinking off).
