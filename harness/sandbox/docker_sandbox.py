"""Docker-backed sandbox. Works with Docker Desktop or Colima (docker.sock)."""
from __future__ import annotations
import io, shlex, tarfile, time, uuid
from pathlib import Path
import docker
from .base import Sandbox, ExecResult


class DockerSandbox(Sandbox):
    def __init__(self, image: str = "qwen-sandbox:latest", network: bool = False, mem_limit: str = "2g",
                 cpus: float = 2.0, dockerfile_dir: Path | None = None, name_prefix: str = "qwen-sbx"):
        self.image, self.network, self.mem_limit, self.cpus = image, network, mem_limit, cpus
        self.dockerfile_dir = dockerfile_dir
        self.name = f"{name_prefix}-{uuid.uuid4().hex[:8]}"
        self.client = docker.from_env()
        self.container = None

    def start(self):
        image = self.image
        if self.dockerfile_dir and (self.dockerfile_dir / "Dockerfile").exists():
            image = f"{self.image.split(':')[0]}-{self.dockerfile_dir.parent.name}:latest"
            self.client.images.build(path=str(self.dockerfile_dir), tag=image, rm=True,
                                     buildargs={"BASE_IMAGE": self.image})
        self.container = self.client.containers.run(
            image, command="sleep infinity", name=self.name, detach=True, tty=False,
            working_dir=self.workdir, network_mode="bridge" if self.network else "none",
            mem_limit=self.mem_limit, nano_cpus=int(self.cpus * 1e9), pids_limit=512,
            labels={"qwen-harness": "1"})
        self.exec("mkdir -p /logs/verifier /tests /app", timeout=30)

    def exec(self, cmd: str, timeout: int = 120, cwd: str | None = None) -> ExecResult:
        cwd = cwd or self.workdir
        wrapped = f"cd {shlex.quote(cwd)} 2>/dev/null || cd /app; timeout -s KILL {timeout} bash -c {shlex.quote(cmd)}"
        res = self.container.exec_run(["bash", "-c", wrapped], demux=True, workdir=self.workdir)
        out, err = res.output
        out = (out or b"").decode("utf-8", "replace"); err = (err or b"").decode("utf-8", "replace")
        timed_out = res.exit_code == 137
        return ExecResult(exit_code=res.exit_code, stdout=out, stderr=err, timed_out=timed_out)

    def write_file(self, path: str, content: str):
        self._put(path, content.encode())

    def read_file(self, path: str) -> str:
        r = self.exec(f"cat {shlex.quote(path)}", timeout=30)
        if r.exit_code != 0: raise FileNotFoundError(r.stderr.strip() or path)
        return r.stdout

    def upload_dir(self, local: Path, remote: str):
        self.exec(f"mkdir -p {shlex.quote(remote)}", timeout=30)
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w") as tar:
            for p in local.rglob("*"):
                if p.name == "Dockerfile" and p.parent == local: continue
                tar.add(p, arcname=str(p.relative_to(local)))
        buf.seek(0); self.container.put_archive(remote, buf.getvalue())

    def _put(self, path: str, data: bytes):
        d, name = path.rsplit("/", 1) if "/" in path else (self.workdir, path)
        d = d or "/"
        self.exec(f"mkdir -p {shlex.quote(d)}", timeout=30)
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w") as tar:
            info = tarfile.TarInfo(name=name); info.size = len(data); info.mtime = int(time.time()); info.mode = 0o644
            tar.addfile(info, io.BytesIO(data))
        buf.seek(0); self.container.put_archive(d, buf.getvalue())

    def stop(self):
        if self.container:
            try: self.container.remove(force=True)
            except Exception: pass
            self.container = None
