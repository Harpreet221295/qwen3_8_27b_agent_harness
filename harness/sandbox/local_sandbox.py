"""NO isolation. Runs in a temp dir on the host. Only for debugging the harness itself."""
from __future__ import annotations
import os, re, shutil, subprocess, sys, tempfile
from pathlib import Path
from .base import Sandbox, ExecResult


class LocalSandbox(Sandbox):
    def __init__(self, **_):
        self.root = None

    def start(self):
        self.root = Path(tempfile.mkdtemp(prefix="qwen-local-sbx-"))
        for d in ["app", "tests", "logs/verifier"]: (self.root / d).mkdir(parents=True)
        self.workdir = str(self.root / "app")
        # host shims: `python` -> this interpreter, `timeout` -> tiny python shim (macOS has neither)
        binp = self.root / "bin"; binp.mkdir()
        (binp / "python").write_text(f"#!/usr/bin/env bash\nexec {sys.executable!r} \"$@\"\n"); (binp / "python").chmod(0o755)
        (binp / "timeout").write_text("#!/usr/bin/env bash\nsecs=$1; shift; perl -e 'alarm shift; exec @ARGV' \"$secs\" \"$@\"\n")
        (binp / "timeout").chmod(0o755)

    def _map(self, p: str) -> str:
        for pre in ["/app", "/tests", "/logs"]:
            if p == pre or p.startswith(pre + "/"): return str(self.root / p.lstrip("/"))
        return p

    def exec(self, cmd: str, timeout: int = 120, cwd: str | None = None) -> ExecResult:
        cwd = self._map(cwd or "/app")
        env = dict(os.environ, APP_DIR=self.workdir, PATH=f"{self.root / 'bin'}:{os.environ.get('PATH', '')}")
        cmd = self._rewrite(cmd)  # absolute /app,/tests,/logs paths -> temp dir
        try:
            p = subprocess.run(["bash", "-c", cmd], cwd=cwd, capture_output=True, text=True, timeout=timeout, env=env)
            return ExecResult(p.returncode, p.stdout, p.stderr)
        except subprocess.TimeoutExpired as e:
            return ExecResult(137, (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or ""),
                              "timed out", timed_out=True)

    _PATH_RE = re.compile(r"(?<![\w/.])/(app|tests|logs)(?=/|\b)")

    def _rewrite(self, text: str) -> str:
        return self._PATH_RE.sub(lambda m: str(self.root / m.group(1)), text)

    def write_file(self, path: str, content: str):
        p = Path(self._map(path)); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(self._rewrite(content))

    def read_file(self, path: str) -> str:
        return Path(self._map(path)).read_text()

    def upload_dir(self, local: Path, remote: str):
        dst = Path(self._map(remote)); dst.mkdir(parents=True, exist_ok=True)
        shutil.copytree(local, dst, dirs_exist_ok=True, ignore=shutil.ignore_patterns("Dockerfile"))
        for f in dst.rglob("*"):  # text files may hard-code /app, /tests, /logs
            if f.is_file() and f.suffix in {".sh", ".py", ".md", ".txt", ".toml", ".sql"}:
                try: f.write_text(self._rewrite(f.read_text()))
                except UnicodeDecodeError: pass

    def stop(self):
        if self.root: shutil.rmtree(self.root, ignore_errors=True)
