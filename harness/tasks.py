from __future__ import annotations
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

TASKS_DIR = Path(__file__).resolve().parent.parent / "tasks"


@dataclass
class Task:
    name: str
    path: Path
    instruction: str
    difficulty: str = "medium"
    tags: list[str] = field(default_factory=list)
    max_steps: int = 30
    agent_timeout_s: int = 900
    test_timeout_s: int = 300
    network: bool = False

    @property
    def env_dir(self) -> Path: return self.path / "environment"
    @property
    def tests_dir(self) -> Path: return self.path / "tests"
    @property
    def solution(self) -> Path: return self.path / "solution" / "solve.sh"


def load_task(path: Path) -> Task:
    meta = tomllib.loads((path / "task.toml").read_text()) if (path / "task.toml").exists() else {}
    t = meta.get("task", meta)
    return Task(name=path.name, path=path, instruction=(path / "instruction.md").read_text().strip(),
                difficulty=t.get("difficulty", "medium"), tags=t.get("tags", []), max_steps=t.get("max_steps", 30),
                agent_timeout_s=t.get("agent_timeout_s", 900), test_timeout_s=t.get("test_timeout_s", 300),
                network=t.get("network", False))


def load_tasks(root: Path = TASKS_DIR, only: list[str] | None = None, tag: str | None = None) -> list[Task]:
    tasks = [load_task(p) for p in sorted(root.iterdir()) if (p / "instruction.md").exists()]
    if only: tasks = [t for t in tasks if t.name in only]
    if tag: tasks = [t for t in tasks if tag in t.tags]
    return tasks
