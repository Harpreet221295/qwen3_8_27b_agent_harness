# Running the official Terminal-Bench 2 against the RunPod endpoint

Our `tasks/` are a small, fast, self-made set. For a number you can compare with public leaderboards, run
Terminal-Bench 2 through **Harbor** (the framework that replaced the `tb` CLI) with the Terminus 2 agent,
pointing it at the vLLM server via LiteLLM's OpenAI-compatible provider.

```bash
pip install harbor
export OPENAI_API_BASE=https://<POD_ID>-8000.proxy.runpod.net/v1     # LiteLLM reads these
export OPENAI_API_KEY=<VLLM_API_KEY>

# smoke: 3 tasks, 1 attempt each
harbor run -d terminal-bench@2.0 -a terminus-2 -m openai/qwen3.8-27b --n-tasks 3

# full: 89 tasks × 3 attempts, 4 concurrent sandboxes (each is a Docker container)
harbor run -d terminal-bench@2.0 -a terminus-2 -m openai/qwen3.8-27b --n-attempts 3 --n-concurrent 4
```
Notes
- Model name after `openai/` must match `--served-model-name` in `serve.sh` (`qwen3.8-27b`).
- Harbor needs Docker locally (Colima works). Some tasks pull large images; give Colima ≥ 60 GB disk.
- Set thinking mode via LiteLLM `extra_body` if you want low reasoning effort; default is xhigh, which is
  slow but is what Qwen reports numbers with.
- Leaderboard context: Terminal-Bench 2.1 is scored with Terminus 2 in E2B sandboxes, pass@1 over 3 repeats.
- The task format used by `tasks/` here mirrors Harbor's (`instruction.md`, `tests/test.sh`,
  `/logs/verifier/reward.txt`), so a task you write here can be moved into Harbor with little change.

Sources: https://www.harborframework.com/docs/tasks · https://artificialanalysis.ai/evaluations/terminalbench-2-1
