from .base import Sandbox, ExecResult

def make_sandbox(kind: str, **kw) -> Sandbox:
    if kind == "docker":
        from .docker_sandbox import DockerSandbox; return DockerSandbox(**kw)
    if kind == "local":
        from .local_sandbox import LocalSandbox; return LocalSandbox(**kw)
    if kind == "e2b":
        from .e2b_sandbox import E2BSandbox; return E2BSandbox(**kw)
    raise ValueError(f"unknown sandbox {kind}")
