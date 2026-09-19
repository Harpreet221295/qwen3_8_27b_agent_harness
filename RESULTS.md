# Results — off 

**Overall: 12/12 = 100%**

| task | diff | pass | avg steps | avg s | avg gen toks | stop reasons |
|---|---|---|---|---|---|---|
| api_server_bugfix | hard | 1/1 | 10.0 | 62 | 1272 | finish |
| csv_report | easy | 1/1 | 5.0 | 30 | 672 | finish |
| debug_traceback | medium | 1/1 | 5.0 | 22 | 474 | finish |
| env_setup_package | medium | 1/1 | 6.0 | 26 | 375 | finish |
| file_organize | easy | 1/1 | 4.0 | 23 | 551 | finish |
| fix_failing_test | easy | 1/1 | 5.0 | 31 | 484 | finish |
| git_workflow | medium | 1/1 | 6.0 | 32 | 511 | finish |
| implement_cli_wordcount | easy | 1/1 | 20.0 | 147 | 3505 | max_steps |
| log_analysis_bash | easy | 1/1 | 4.0 | 22 | 557 | finish |
| make_build_c | medium | 1/1 | 6.0 | 37 | 933 | finish |
| refactor_to_package | medium | 1/1 | 5.0 | 28 | 693 | finish |
| sqlite_query | medium | 1/1 | 5.0 | 30 | 725 | finish |

Run: `python run_eval.py --sandbox docker --parallel 3`, thinking off, 1 attempt per task, 2026-09-19.
Model: Qwen/Qwen3.8-27B BF16 on 1× A100 SXM 80GB via vLLM. Sandbox: Docker via Colima on an M1 MacBook Air.

Observations
- 12/12 on the starter set, so this set is too easy to separate models; next step is harder tasks and pass@3.
- Typical task: 4–6 steps, 22–37 s wall, 400–900 generated tokens. Multiple edits are issued in one turn (parallel tool calls).
- `implement_cli_wordcount` passed the grader but hit the 20-step cap without calling finish: the model kept re-verifying edge cases.
- `api_server_bugfix` (hard): 10 steps, started the server in the background, ran the checker, fixed all 6 bugs, stopped the server.
- Zero fallback parses: every tool call came back structured through `--tool-call-parser qwen3_xml`.
