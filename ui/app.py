"""Agent run console. Run:  .venv/bin/python -m uvicorn ui.app:app --port 7861   → http://localhost:7861
Pick a task (or type your own instruction), watch reasoning / tool calls / outputs stream live, see the grade."""
from __future__ import annotations
import asyncio, json, queue, threading, time, traceback, uuid
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from harness import config
from harness.agent import Agent
from harness.runner import RESULTS_DIR
from harness.sandbox import make_sandbox
from harness.tasks import load_tasks, TASKS_DIR
from harness.tools import ToolExecutor

STATIC = Path(__file__).resolve().parent / "static"
app = FastAPI(title="Qwen agent console")
app.mount("/static", StaticFiles(directory=STATIC), name="static")
STOP_FLAGS: dict[str, threading.Event] = {}


def sse(event: str, data) -> str:
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"


@app.get("/")
async def index(): return FileResponse(STATIC / "index.html")


@app.get("/api/info")
async def info():
    import docker
    try: docker.from_env().ping(); dk = True
    except Exception: dk = False
    return {"base_url": config.BASE_URL, "model": config.MODEL, "sandbox_image": config.SANDBOX_IMAGE, "docker": dk}


@app.get("/api/tasks")
async def tasks():
    return [{"name": t.name, "difficulty": t.difficulty, "tags": t.tags, "max_steps": t.max_steps, "instruction": t.instruction} for t in load_tasks()]


@app.get("/api/runs")
async def runs():
    out = []
    for d in sorted(RESULTS_DIR.iterdir(), reverse=True):
        if (d / "summary.json").exists():
            s = json.loads((d / "summary.json").read_text())
            out.append({"run_id": d.name, "passed": s.get("overall_pass"), "n": s.get("overall_n"), "markdown": s.get("markdown", "")})
    return out


@app.get("/api/runs/{run_id}")
async def run_detail(run_id: str):
    d = RESULTS_DIR / run_id
    if not d.is_dir(): return JSONResponse({"error": "not found"}, status_code=404)
    return [json.loads(p.read_text()) for p in sorted(d.glob("*_r*.json"))]


@app.post("/api/stop/{job}")
async def stop(job: str):
    if job in STOP_FLAGS: STOP_FLAGS[job].set(); return {"ok": True}
    return {"ok": False}


@app.post("/api/run")
async def run(req: Request):
    body = await req.json()
    task_name = body.get("task"); custom = (body.get("instruction") or "").strip()
    sandbox_kind = body.get("sandbox", "docker"); thinking = body.get("thinking", "off")
    max_steps = int(body.get("max_steps", 30)); max_tokens = int(body.get("max_tokens", 4096 if thinking == "off" else 16384))
    grade = bool(body.get("grade", True)) and bool(task_name) and not custom   # custom text = no grader
    task = next((t for t in load_tasks() if t.name == task_name), None) if task_name else None
    instruction = custom or (task.instruction if task else "")
    if not instruction: return JSONResponse({"error": "no task or instruction"}, status_code=400)
    job = uuid.uuid4().hex[:8]; STOP_FLAGS[job] = threading.Event()
    q: queue.Queue = queue.Queue()
    emit = lambda kind, data: q.put((kind, data))

    def worker():
        rec = {"task": (task_name if not custom else "custom"), "rep": 0, "mode": "agent", "thinking": thinking, "model": config.MODEL,
               "reward": None, "passed": None, "started": datetime.now().isoformat(), "instruction": instruction}
        t0 = time.time()
        try:
            sb_kw = {"image": config.SANDBOX_IMAGE, "network": bool(body.get("network", False)) or bool(task and task.network),
                     "dockerfile_dir": task.env_dir if task and (task.env_dir / "Dockerfile").exists() else None}
            emit("status", {"t": f"starting {sandbox_kind} sandbox… " + ("(task files loaded, custom instruction, no grading)" if task and custom else "(graded)" if grade else "(no grading)")})
            with make_sandbox(sandbox_kind, **sb_kw) as sb:
                if task and task.env_dir.exists(): sb.upload_dir(task.env_dir, "/app")
                if task and (task.env_dir / "setup.sh").exists(): sb.exec("bash /app/setup.sh && rm -f /app/setup.sh", timeout=300)
                emit("status", {"t": "sandbox ready, agent starting"})
                agent = Agent(ToolExecutor(sb), thinking=thinking, max_steps=max_steps, max_tokens=max_tokens,
                              on_event=emit, should_stop=STOP_FLAGS[job].is_set)
                res = agent.run(instruction)
                rec.update({k: v for k, v in res.__dict__.items() if k != "transcript"}); rec["transcript"] = res.transcript
                if grade:
                    emit("status", {"t": "grading…"})
                    sb.upload_dir(task.tests_dir, "/tests"); sb.exec("rm -f /logs/verifier/reward.txt", timeout=10)
                    r = sb.exec("bash /tests/test.sh", timeout=task.test_timeout_s, cwd="/app")
                    try: rec["reward"] = float(sb.read_file("/logs/verifier/reward.txt").strip().splitlines()[0])
                    except Exception: rec["reward"] = 0.0
                    rec["passed"] = rec["reward"] >= 1.0; rec["test_output"] = r.output[-3000:]
                    emit("grade", {"passed": rec["passed"], "reward": rec["reward"], "test_output": r.output[-3000:]})
        except Exception as e:
            rec["harness_error"] = f"{type(e).__name__}: {e}"; emit("error", {"message": rec["harness_error"], "trace": traceback.format_exc()[-1200:]})
        rec["wall_s"] = round(time.time() - t0, 1)
        out = RESULTS_DIR / "ui_runs"; out.mkdir(parents=True, exist_ok=True)
        p = out / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{rec['task']}_{job}.json"; p.write_text(json.dumps(rec, indent=1, default=str))
        emit("saved", {"path": str(p.relative_to(RESULTS_DIR.parent))}); q.put(None); STOP_FLAGS.pop(job, None)

    threading.Thread(target=worker, daemon=True).start()

    async def gen():
        yield sse("job", {"job": job})
        while True:
            item = await asyncio.to_thread(q.get)
            if item is None: yield sse("end", {}); break
            yield sse(*item)
    return StreamingResponse(gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
