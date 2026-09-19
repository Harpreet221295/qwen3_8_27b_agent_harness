"""Exercise the agent loop + tools + local sandbox with a scripted fake model (no endpoint needed).
Run: .venv/bin/python -m pytest tests/ -q
"""
import json
from types import SimpleNamespace as NS
from harness.agent import Agent
from harness.sandbox.local_sandbox import LocalSandbox
from harness.tools import ToolExecutor


def resp(content="", tool_calls=None, reasoning=None, finish="stop"):
    tcs = [NS(id=f"c{i}", function=NS(name=n, arguments=json.dumps(a))) for i, (n, a) in enumerate(tool_calls or [])]
    msg = NS(content=content, tool_calls=tcs or None, reasoning_content=reasoning)
    return NS(choices=[NS(message=msg, finish_reason=finish)], usage=NS(prompt_tokens=10, completion_tokens=5))


class FakeCompletions:
    def __init__(self, script): self.script = list(script); self.calls = []
    def create(self, **kw): self.calls.append(kw); return self.script.pop(0)


def make_agent(script, **kw):
    sb = LocalSandbox(); sb.start()
    ag = Agent(ToolExecutor(sb), thinking="off", max_steps=10, stream=False, **kw)  # fake client is non-streaming
    ag.client = NS(chat=NS(completions=FakeCompletions(script)))
    return ag, sb


def test_full_loop_with_structured_tool_calls():
    script = [
        resp(tool_calls=[("bash", {"command": "mkdir -p src && cd src && pwd"})]),
        resp(tool_calls=[("write_file", {"path": "hello.py", "content": "print('hi')\n"})]),   # relative to cwd (src/)
        resp(tool_calls=[("edit_file", {"path": "hello.py", "old_string": "hi", "new_string": "hello"})]),
        resp(tool_calls=[("read_file", {"path": "hello.py"}), ("bash", {"command": "python hello.py"})]),
        resp(tool_calls=[("finish", {"summary": "done"})]),
    ]
    ag, sb = make_agent(script)
    try:
        r = ag.run("make hello")
        assert r.finished and r.stop_reason == "finish" and r.steps == 5
        outs = [tc["output"] for e in r.transcript for tc in e["tool_calls"]]
        assert outs[0].rstrip().endswith("/src\n[exit code 0]") or "/src" in outs[0]
        assert ag.ex.cwd.endswith("/src"), ag.ex.cwd            # cwd persisted across bash calls
        assert "hello" in sb.read_file("/app/src/hello.py")
        assert "1| print('hello')" in outs[3] and "hello\n[exit code 0]" in outs[4]
        assert r.prompt_tokens == 50 and r.completion_tokens == 25
        # tool results were fed back as role=tool messages
        last_msgs = ag.client.chat.completions.calls[-1]["messages"]
        assert sum(1 for m in last_msgs if m["role"] == "tool") == 6
    finally: sb.stop()


def test_fallback_text_tool_call_and_bad_json():
    raw = '<tool_call>{"name": "bash", "arguments": {"command": "echo fb"}}</tool_call>'
    script = [resp(content=raw),
              resp(tool_calls=[("bash", {"command": "echo x"})]),
              resp(tool_calls=[("finish", {"summary": "ok"})])]
    ag, sb = make_agent(script)
    try:
        r = ag.run("x")
        assert r.fallback_parses == 1 and r.finished
        assert "fb" in r.transcript[0]["tool_calls"][0]["output"]
    finally: sb.stop()


def test_no_tool_call_nudge_then_stop():
    script = [resp(content="I think it's done."), resp(content="Yes, done.")]
    ag, sb = make_agent(script)
    try:
        r = ag.run("x")
        assert not r.finished and r.stop_reason == "no_tool_call" and r.steps == 2
    finally: sb.stop()


def test_max_steps_and_timeout_and_errors():
    script = [resp(tool_calls=[("bash", {"command": "sleep 5", "timeout": 1})]),
              resp(tool_calls=[("read_file", {"path": "missing.txt"})]),
              resp(tool_calls=[("edit_file", {"path": "missing.txt", "old_string": "a", "new_string": "b"})]),
              resp(tool_calls=[("nope", {})])]
    ag, sb = make_agent(script); ag.max_steps = 4
    try:
        r = ag.run("x")
        outs = [tc["output"] for e in r.transcript for tc in e["tool_calls"]]
        assert "killed after 1s" in outs[0] and "exit code 137" in outs[0]
        assert outs[1].startswith("error:") and outs[2].startswith("error:") and "unknown tool" in outs[3]
        assert r.stop_reason == "max_steps"
    finally: sb.stop()


def test_output_truncation():
    script = [resp(tool_calls=[("bash", {"command": "python -c \"print('x'*20000)\""})]),
              resp(tool_calls=[("finish", {"summary": "ok"})])]
    ag, sb = make_agent(script)
    try:
        ag.run("x")
        tool_msg = [m for m in ag.client.chat.completions.calls[-1]["messages"] if m["role"] == "tool"][0]["content"]
        assert "chars truncated" in tool_msg and len(tool_msg) < 7000
    finally: sb.stop()
