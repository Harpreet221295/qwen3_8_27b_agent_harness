from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExecResult:
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False

    @property
    def output(self) -> str:
        out = self.stdout
        if self.stderr: out += ("\n" if out else "") + "[stderr]\n" + self.stderr
        return out


class Sandbox(ABC):
    """A throwaway Linux workspace. /app is the working dir; /tests and /logs are for the grader."""
    workdir = "/app"

    @abstractmethod
    def start(self) -> None: ...
    @abstractmethod
    def exec(self, cmd: str, timeout: int = 120, cwd: str | None = None) -> ExecResult: ...
    @abstractmethod
    def write_file(self, path: str, content: str) -> None: ...
    @abstractmethod
    def read_file(self, path: str) -> str: ...
    @abstractmethod
    def upload_dir(self, local: Path, remote: str) -> None: ...
    @abstractmethod
    def stop(self) -> None: ...

    def __enter__(self): self.start(); return self
    def __exit__(self, *a): self.stop()
