"""Tool definitions (OpenAI function-calling schema) and their sandbox-backed implementations."""
from __future__ import annotations
import json
from .sandbox.base import Sandbox

MAX_OUTPUT_CHARS = 6000

TOOLS = [
    {"type": "function", "function": {
        "name": "bash",
        "description": "Run a bash command in the sandbox. The working directory persists between calls (cd works). "
                       "Output is truncated. Use for ls, cat, grep, git, python, pytest, make, etc.",
        "parameters": {"type": "object", "properties": {
            "command": {"type": "string", "description": "The command to run"},
            "timeout": {"type": "integer", "description": "Seconds before the command is killed (default 120)"}},
            "required": ["command"]}}},
    {"type": "function", "function": {
        "name": "read_file",
        "description": "Read a text file. Optionally a line range (1-indexed, inclusive).",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string"}, "start_line": {"type": "integer"}, "end_line": {"type": "integer"}},
            "required": ["path"]}}},
    {"type": "function", "function": {
        "name": "write_file",
        "description": "Create or overwrite a text file with the given content. Parent directories are created.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                       "required": ["path", "content"]}}},
    {"type": "function", "function": {
        "name": "edit_file",
        "description": "Replace an exact substring in a file with new text. old_string must appear exactly once.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string"}, "old_string": {"type": "string"}, "new_string": {"type": "string"}},
            "required": ["path", "old_string", "new_string"]}}},
    {"type": "function", "function": {
        "name": "finish",
        "description": "Call when the task is complete (or cannot be completed). Give a short summary of what you did.",
        "parameters": {"type": "object", "properties": {"summary": {"type": "string"}}, "required": ["summary"]}}},
]


def truncate(s: str, n: int = MAX_OUTPUT_CHARS) -> str:
    if len(s) <= n: return s
    half = n // 2
    return s[:half] + f"\n... [{len(s) - n} chars truncated] ...\n" + s[-half:]


class ToolExecutor:
    def __init__(self, sandbox: Sandbox):
        self.sb = sandbox; self.cwd = sandbox.workdir

    def _abs(self, path: str) -> str:
        return path if path.startswith("/") else f"{self.cwd.rstrip('/')}/{path}"

    def run(self, name: str, args: dict) -> str:
        try:
            fn = getattr(self, f"t_{name}")
        except AttributeError:
            return f"error: unknown tool {name}"
        try:
            return truncate(fn(**args))
        except TypeError as e:
            return f"error: bad arguments for {name}: {e}"
        except Exception as e:
            return f"error: {type(e).__name__}: {e}"

    def t_bash(self, command: str, timeout: int = 120) -> str:
        timeout = max(1, min(int(timeout or 120), 600))
        marker = "__QWEN_CWD__"
        r = self.sb.exec(f"{command}\nprintf '\\n{marker}%s' \"$PWD\"", timeout=timeout, cwd=self.cwd)
        out = r.stdout
        if marker in out:
            out, _, newcwd = out.rpartition(marker)
            if newcwd.strip(): self.cwd = newcwd.strip()
        text = out.rstrip("\n")
        if r.stderr.strip(): text += ("\n" if text else "") + "[stderr]\n" + r.stderr.rstrip("\n")
        if r.timed_out: text += f"\n[command killed after {timeout}s]"
        return f"{text}\n[exit code {r.exit_code}]"

    def t_read_file(self, path: str, start_line: int | None = None, end_line: int | None = None) -> str:
        content = self.sb.read_file(self._abs(path))
        lines = content.splitlines()
        s = (start_line or 1) - 1; e = end_line or len(lines)
        return "\n".join(f"{i+1:>5}| {l}" for i, l in enumerate(lines[s:e], start=s))

    def t_write_file(self, path: str, content: str) -> str:
        self.sb.write_file(self._abs(path), content)
        return f"wrote {len(content)} chars to {path}"

    def t_edit_file(self, path: str, old_string: str, new_string: str) -> str:
        p = self._abs(path); content = self.sb.read_file(p)
        n = content.count(old_string)
        if n == 0: return "error: old_string not found in file"
        if n > 1: return f"error: old_string occurs {n} times; make it unique"
        self.sb.write_file(p, content.replace(old_string, new_string, 1))
        return f"edited {path}"

    def t_finish(self, summary: str = "") -> str:
        return "FINISHED: " + summary
