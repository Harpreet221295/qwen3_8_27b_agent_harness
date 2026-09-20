"""The agent loop: model <-> tools, with transcript, step/token budgets, live events and a fallback tool-call parser."""
from __future__ import annotations
import json, re, time
from dataclasses import dataclass, field
from typing import Callable
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

CHAT_SYSTEM_PROMPT = """You are a software engineering agent working in a persistent Linux sandbox with the user.
The workspace is /app (your current directory). Tools: bash, read_file, write_file, edit_file, finish.
Files and state persist across the whole conversation, so build on your earlier work.

Rules:
- When the user asks for work, do it with tools: inspect, change, verify by running it.
- When the user just chats, asks a question, or nothing needs doing, reply in plain text without tools.
- Call finish only when a requested piece of work is complete and verified; put a short summary in it.
- Do not invent results; report what the tools actually showed.
"""

FALLBACK_RE = re.compile(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", re.S)
EventFn = Callable[[str, dict], None]


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
                 model: str | None = None, temperature: float | None = None, verbose: bool = False,
                 on_event: EventFn | None = None, stream: bool = True, should_stop: Callable[[], bool] | None = None,
                 chat_mode: bool = False):
        self.ex, self.thinking, self.max_steps, self.max_tokens = executor, thinking, max_steps, max_tokens
        self.chat_mode = chat_mode
        self.model = model or config.MODEL; self.verbose = verbose
        self.on_event = on_event or (lambda kind, data: None); self.stream = stream
        self.should_stop = should_stop or (lambda: False)
        self.client = OpenAI(base_url=config.BASE_URL, api_key=config.API_KEY, timeout=900)
        if thinking == "off":
            self.sampling = dict(temperature=0.7 if temperature is None else temperature, top_p=0.8,
                                 extra_body={"top_k": 20, "presence_penalty": 1.5, "chat_template_kwargs": {"enable_thinking": False}})
        else:
            self.sampling = dict(temperature=1.0 if temperature is None else temperature, top_p=0.95,
                                 extra_body={"top_k": 20, "chat_template_kwargs": {"reasoning_effort": thinking}})

    def log(self, *a):
        if self.verbose: print(*a, flush=True)

    # ---- one model turn -> (content, reasoning, calls, usage, finish_reason) ----
    def _turn(self, msgs):
        if self.stream:
            try: return self._turn_stream(msgs)
            except Exception as e:
                self.log("stream failed, falling back to non-stream:", e)
        r = self.client.chat.completions.create(model=self.model, messages=msgs, tools=TOOLS, tool_choice="auto",
                                                max_tokens=self.max_tokens, **self.sampling)
        m = r.choices[0].message
        reasoning = getattr(m, "reasoning_content", None) or getattr(m, "reasoning", None) or ""
        if reasoning: self.on_event("reasoning", {"t": reasoning})
        if m.content: self.on_event("content", {"t": m.content})
        calls = [(t.id, t.function.name, t.function.arguments) for t in (m.tool_calls or [])]
        return m.content or "", reasoning, calls, r.usage, r.choices[0].finish_reason

    def _turn_stream(self, msgs):
        content, reasoning, calls, usage, finish = [], [], {}, None, None
        stream = self.client.chat.completions.create(model=self.model, messages=msgs, tools=TOOLS, tool_choice="auto",
                                                     max_tokens=self.max_tokens, stream=True,
                                                     stream_options={"include_usage": True}, **self.sampling)
        for chunk in stream:
            if chunk.usage: usage = chunk.usage
            if not chunk.choices: continue
            ch = chunk.choices[0]; d = ch.delta
            if ch.finish_reason: finish = ch.finish_reason
            rc = getattr(d, "reasoning_content", None) or getattr(d, "reasoning", None)
            if rc: reasoning.append(rc); self.on_event("reasoning", {"t": rc})
            if d.content: content.append(d.content); self.on_event("content", {"t": d.content})
            for tc in (d.tool_calls or []):
                c = calls.setdefault(tc.index, {"id": tc.id or f"call_{tc.index}", "name": "", "arguments": ""})
                if tc.id: c["id"] = tc.id
                if tc.function and tc.function.name: c["name"] += tc.function.name
                frag = tc.function.arguments if tc.function and tc.function.arguments else ""
                if frag: c["arguments"] += frag
                self.on_event("tool_delta", {"index": tc.index, "name": c["name"], "t": frag})
        return "".join(content), "".join(reasoning), [(c["id"], c["name"], c["arguments"]) for c in calls.values()], usage, finish

    def run(self, instruction: str) -> AgentResult:
        msgs = [{"role": "system", "content": CHAT_SYSTEM_PROMPT if self.chat_mode else SYSTEM_PROMPT}, {"role": "user", "content": instruction}]
        return self.loop(msgs)

    def run_turn(self, msgs: list, user_text: str) -> AgentResult:
        """Session mode: append the user's message to an existing conversation and run until the agent replies or finishes."""
        if not msgs: msgs.append({"role": "system", "content": CHAT_SYSTEM_PROMPT})
        msgs.append({"role": "user", "content": user_text})
        return self.loop(msgs)

    def loop(self, msgs: list) -> AgentResult:
        transcript, t0 = [], time.time()
        ptoks = ctoks = fallback = errors = 0
        for step in range(1, self.max_steps + 1):
            if self.should_stop():
                return self._done(False, step - 1, "stopped", "", ptoks, ctoks, t0, transcript, fallback, errors)
            self.on_event("step", {"step": step, "max_steps": self.max_steps})
            try:
                content, reasoning, calls, usage, finish_reason = self._turn(msgs)
            except Exception as e:
                errors += 1; transcript.append({"step": step, "error": str(e)[:500]}); self.on_event("error", {"message": str(e)[:500]})
                if errors >= 3: return self._done(False, step, f"api_error: {e}", "", ptoks, ctoks, t0, transcript, fallback, errors)
                time.sleep(3); continue
            if usage: ptoks += usage.prompt_tokens; ctoks += usage.completion_tokens
            if not calls:  # fallback: model emitted raw <tool_call> text instead of structured calls
                for i, mm in enumerate(FALLBACK_RE.finditer(content)):
                    try:
                        d = json.loads(mm.group(1)); calls.append((f"fb{step}_{i}", d["name"], json.dumps(d.get("arguments", {})))); fallback += 1
                    except Exception: pass
            entry = {"step": step, "reasoning_chars": len(reasoning), "reasoning": reasoning[:4000], "content": content[:2000], "tool_calls": [], "finish_reason": finish_reason}
            if not calls:
                msgs.append({"role": "assistant", "content": content})
                transcript.append(entry)
                if finish_reason == "length":
                    msgs.append({"role": "user", "content": "Your output was cut off. Continue, using tools. Call finish when done."}); continue
                if self.chat_mode:
                    return self._done(True, step, "reply", content, ptoks, ctoks, t0, transcript, fallback, errors)
                if any(t.get("nudged") for t in transcript[-3:]):
                    return self._done(False, step, "no_tool_call", content, ptoks, ctoks, t0, transcript, fallback, errors)
                entry["nudged"] = True
                msgs.append({"role": "user", "content": "Use the tools to act. If the task is complete, call finish."}); continue

            msgs.append({"role": "assistant", "content": content or None,
                         "tool_calls": [{"id": cid, "type": "function", "function": {"name": n, "arguments": a}} for cid, n, a in calls]})
            for cid, name, argstr in calls:
                try: args = json.loads(argstr) if argstr else {}
                except json.JSONDecodeError: args = None
                self.on_event("tool_call", {"step": step, "name": name, "args": args if args is not None else argstr})
                out = "error: arguments were not valid JSON" if args is None else self.ex.run(name, args)
                self.on_event("tool_result", {"step": step, "name": name, "output": out})
                entry["tool_calls"].append({"name": name, "args": args if args is not None else argstr, "output": out[:3000]})
                self.log(f"[{step}] {name} {json.dumps(args)[:200] if args else argstr[:200]}\n    -> {out[:300]!r}")
                msgs.append({"role": "tool", "tool_call_id": cid, "content": out})
                if name == "finish":
                    transcript.append(entry)
                    return self._done(True, step, "finish", args.get("summary", "") if args else "", ptoks, ctoks, t0, transcript, fallback, errors)
            transcript.append(entry)
        return self._done(False, self.max_steps, "max_steps", "", ptoks, ctoks, t0, transcript, fallback, errors)

    def _done(self, fin, steps, why, summary, p, c, t0, tr, fb, er):
        res = AgentResult(fin, steps, why, summary, p, c, time.time() - t0, tr, fb, er)
        self.on_event("agent_done", {"finished": fin, "steps": steps, "stop_reason": why, "summary": summary,
                                     "prompt_tokens": p, "completion_tokens": c, "wall_s": round(res.wall_s, 1)})
        return res
