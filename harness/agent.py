"""The agent loop: model <-> tools, with transcript, step/token budgets and a fallback tool-call parser."""
from __future__ import annotations
import json, re, time
from dataclasses import dataclass, field
from openai import OpenAI
from . import config
from .tools import TOOLS, ToolExecutor

SYSTEM_PROMPT = """You are an autonomous software engineering agent working in a Linux sandbox.
The project lives in /app (your current directory). You have tools: bash, read_file, write_file, edit_file, finish.

Rules:
- Work step by step: inspect first (ls, cat, run tests), then change files, then verify by running the code/tests.
- Use tools for every action. Do not describe what you would do; do it.
- Prefer edit_file for small changes and write_file for new files.
- Do not ask the user questions; there is no user. Make reasonable assumptions.
- When the task is done and verified, call finish with a one-paragraph summary. Always call finish before stopping.
"""

FALLBACK_RE = re.compile(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", re.S)


@dataclass
class AgentResult:
    finished: bool
    steps: int
    stop_reason: str
    summary: str
    prompt_tokens: int
    completion_tokens: int
    wall_s: float
    transcript: list = field(default_factory=list)
    fallback_parses: int = 0
    errors: int = 0


class Agent:
    def __init__(self, executor: ToolExecutor, thinking: str = "off", max_steps: int = 30, max_tokens: int = 4096,
                 model: str | None = None, temperature: float | None = None, verbose: bool = False):
        self.ex, self.thinking, self.max_steps, self.max_tokens = executor, thinking, max_steps, max_tokens
        self.model = model or config.MODEL; self.verbose = verbose
        self.client = OpenAI(base_url=config.BASE_URL, api_key=config.API_KEY, timeout=900)
        if thinking == "off":
            self.sampling = dict(temperature=0.7 if temperature is None else temperature, top_p=0.8,
                                 extra_body={"top_k": 20, "presence_penalty": 1.5, "chat_template_kwargs": {"enable_thinking": False}})
        else:
            self.sampling = dict(temperature=1.0 if temperature is None else temperature, top_p=0.95,
                                 extra_body={"top_k": 20, "chat_template_kwargs": {"reasoning_effort": thinking}})

    def log(self, *a):
        if self.verbose: print(*a, flush=True)

    def run(self, instruction: str) -> AgentResult:
        msgs = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": instruction}]
        transcript, t0 = [], time.time()
        ptoks = ctoks = fallback = errors = 0
        for step in range(1, self.max_steps + 1):
            try:
                r = self.client.chat.completions.create(model=self.model, messages=msgs, tools=TOOLS, tool_choice="auto",
                                                        max_tokens=self.max_tokens, **self.sampling)
            except Exception as e:
                errors += 1; transcript.append({"step": step, "error": str(e)[:500]})
                if errors >= 3: return self._done(False, step, f"api_error: {e}", "", ptoks, ctoks, t0, transcript, fallback, errors)
                time.sleep(3); continue
            m = r.choices[0].message
            if r.usage: ptoks += r.usage.prompt_tokens; ctoks += r.usage.completion_tokens
            reasoning = getattr(m, "reasoning_content", None) or getattr(m, "reasoning", None) or ""
            calls = [(t.id, t.function.name, t.function.arguments) for t in (m.tool_calls or [])]
            content = m.content or ""
            if not calls:  # fallback: model emitted raw <tool_call> text instead of structured calls
                for i, mm in enumerate(FALLBACK_RE.finditer(content)):
                    try:
                        d = json.loads(mm.group(1)); calls.append((f"fb{step}_{i}", d["name"], json.dumps(d.get("arguments", {})))); fallback += 1
                    except Exception: pass
            entry = {"step": step, "reasoning_chars": len(reasoning), "content": content[:2000], "tool_calls": [], "finish_reason": r.choices[0].finish_reason}
            if not calls:
                msgs.append({"role": "assistant", "content": content})
                transcript.append(entry)
                if r.choices[0].finish_reason == "length":
                    msgs.append({"role": "user", "content": "Your output was cut off. Continue, using tools. Call finish when done."}); continue
                # model stopped without tools: nudge once, then stop
                if entry.get("nudged") or any(t.get("nudged") for t in transcript[-3:]):
                    return self._done(False, step, "no_tool_call", content, ptoks, ctoks, t0, transcript, fallback, errors)
                entry["nudged"] = True
                msgs.append({"role": "user", "content": "Use the tools to act. If the task is complete, call finish."}); continue

            msgs.append({"role": "assistant", "content": content or None,
                         "tool_calls": [{"id": cid, "type": "function", "function": {"name": n, "arguments": a}} for cid, n, a in calls]})
            for cid, name, argstr in calls:
                try: args = json.loads(argstr) if argstr else {}
                except json.JSONDecodeError: args = None
                out = "error: arguments were not valid JSON" if args is None else self.ex.run(name, args)
                entry["tool_calls"].append({"name": name, "args": args if args is not None else argstr, "output": out[:3000]})
                self.log(f"[{step}] {name} {json.dumps(args)[:200] if args else argstr[:200]}\n    -> {out[:300]!r}")
                msgs.append({"role": "tool", "tool_call_id": cid, "content": out})
                if name == "finish":
                    transcript.append(entry)
                    return self._done(True, step, "finish", args.get("summary", "") if args else "", ptoks, ctoks, t0, transcript, fallback, errors)
            transcript.append(entry)
        return self._done(False, self.max_steps, "max_steps", "", ptoks, ctoks, t0, transcript, fallback, errors)

    @staticmethod
    def _done(fin, steps, why, summary, p, c, t0, tr, fb, er):
        return AgentResult(fin, steps, why, summary, p, c, time.time() - t0, tr, fb, er)
