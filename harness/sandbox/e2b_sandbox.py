"""E2B cloud sandbox (Firecracker microVM). pip install e2b-code-interpreter; export E2B_API_KEY."""
from __future__ import annotations
import shlex
from pathlib import Path
from .base import Sandbox, ExecResult


class E2BSandbox(Sandbox):
    def __init__(self, template: str | None = None, timeout_s: int = 1800, **_):
        self.template, self.timeout_s, self.sbx = template, timeout_s, None

    def start(self):
        from e2b_code_interpreter import Sandbox as E2B
        self.sbx = E2B.create(template=self.template, timeout=self.timeout_s) if self.template else E2B.create(timeout=self.timeout_s)
        self.exec("sudo mkdir -p /app /tests /logs/verifier && sudo chmod -R 777 /app /tests /logs; "
                  "sudo apt-get install -y -qq jq sqlite3 >/dev/null 2>&1 || true; pip install -q pytest || true", timeout=300)

    def exec(self, cmd: str, timeout: int = 120, cwd: str | None = None) -> ExecResult:
        cwd = cwd or self.workdir
        try:
            r = self.sbx.commands.run(f"cd {shlex.quote(cwd)} 2>/dev/null || cd /app; {cmd}", timeout=timeout)
            return ExecResult(r.exit_code, r.stdout, r.stderr)
        except Exception as e:  # CommandExitException / TimeoutException
            code = getattr(e, "exit_code", 1); out = getattr(e, "stdout", ""); err = getattr(e, "stderr", str(e))
            return ExecResult(code, out, err, timed_out="timeout" in str(e).lower())

    def write_file(self, path: str, content: str): self.sbx.files.write(path, content)
    def read_file(self, path: str) -> str: return self.sbx.files.read(path)

    def upload_dir(self, local: Path, remote: str):
        for p in local.rglob("*"):
            if p.is_file() and not (p.name == "Dockerfile" and p.parent == local):
                self.sbx.files.write(f"{remote}/{p.relative_to(local)}", p.read_bytes())

    def stop(self):
        if self.sbx:
            try: self.sbx.kill()
            except Exception: pass
