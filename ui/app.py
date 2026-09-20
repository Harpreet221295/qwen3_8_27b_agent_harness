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


# ======================= persistent sessions (chat with the agent in one long-lived sandbox) =======================
SESSIONS: dict[str, dict] = {}
SESS_DIR = RESULTS_DIR / "sessions"
SESS_LOCK = threading.Lock()


def _sess_public(s: dict) -> dict:
    return {"id": s["id"], "title": s["title"], "created": s["created"], "thinking": s["thinking"], "sandbox": s["sandbox_kind"],
            "task": s["task"], "alive": s["sb"] is not None, "turns": len(s["turns"]), "busy": s["busy"]}


def _sess_save(s: dict):
    SESS_DIR.mkdir(parents=True, exist_ok=True)
    (SESS_DIR / f"{s['id']}.json").write_text(json.dumps({k: v for k, v in s.items() if k not in ("sb", "ex", "msgs", "stop")} | {"messages": s["msgs"]}, indent=1, default=str))


@app.get("/api/sessions")
async def sessions_list():
    live = {sid: _sess_public(s) for sid, s in SESSIONS.items()}
    if SESS_DIR.exists():
        for p in SESS_DIR.glob("*.json"):
            if p.stem not in live:
                d = json.loads(p.read_text())
                live[p.stem] = {"id": d["id"], "title": d["title"], "created": d["created"], "thinking": d["thinking"], "sandbox": d["sandbox_kind"],
                                "task": d["task"], "alive": False, "turns": len(d["turns"]), "busy": False}
    return sorted(live.values(), key=lambda x: x["created"], reverse=True)


@app.get("/api/sessions/{sid}")
async def session_detail(sid: str):
    if sid in SESSIONS:
        s = SESSIONS[sid]; return _sess_public(s) | {"turns": s["turns"]}
    p = SESS_DIR / f"{sid}.json"
    if not p.exists(): return JSONResponse({"error": "not found"}, status_code=404)
    d = json.loads(p.read_text()); return {"id": d["id"], "title": d["title"], "alive": False, "turns": d["turns"], "thinking": d["thinking"], "task": d["task"]}


@app.post("/api/sessions")
async def session_create(req: Request):
    body = await req.json()
    sandbox_kind = body.get("sandbox", "docker"); thinking = body.get("thinking", "off"); task_name = body.get("task") or None
    task = next((t for t in load_tasks() if t.name == task_name), None) if task_name else None
    sid = uuid.uuid4().hex[:8]
    sb_kw = {"image": config.SANDBOX_IMAGE, "network": bool(body.get("network", False)),
             "dockerfile_dir": task.env_dir if task and (task.env_dir / "Dockerfile").exists() else None}
    def start():
        sb = make_sandbox(sandbox_kind, **sb_kw); sb.start()
        if task and task.env_dir.exists(): sb.upload_dir(task.env_dir, "/app")
        if task and (task.env_dir / "setup.sh").exists(): sb.exec("bash /app/setup.sh && rm -f /app/setup.sh", timeout=300)
        return sb
    try: sb = await asyncio.to_thread(start)
    except Exception as e: return JSONResponse({"error": f"sandbox failed: {e}"}, status_code=500)
    s = {"id": sid, "title": body.get("title") or (f"{task_name} session" if task_name else "new session"), "created": datetime.now().isoformat(),
         "thinking": thinking, "sandbox_kind": sandbox_kind, "task": task_name, "sb": sb, "ex": ToolExecutor(sb), "msgs": [], "turns": [],
         "busy": False, "stop": threading.Event(), "max_steps": int(body.get("max_steps", 40))}
    with SESS_LOCK: SESSIONS[sid] = s
    _sess_save(s)
    return _sess_public(s)


@app.delete("/api/sessions/{sid}")
async def session_close(sid: str):
    s = SESSIONS.pop(sid, None)
    if not s: return {"ok": False}
    try: await asyncio.to_thread(s["sb"].stop)
    except Exception: pass
    s["sb"] = None; _sess_save(s); return {"ok": True}


@app.post("/api/sessions/{sid}/stop")
async def session_stop_turn(sid: str):
    if sid in SESSIONS: SESSIONS[sid]["stop"].set(); return {"ok": True}
    return {"ok": False}


@app.post("/api/sessions/{sid}/message")
async def session_message(sid: str, req: Request):
    s = SESSIONS.get(sid)
    if not s or s["sb"] is None: return JSONResponse({"error": "session not alive (create a new one)"}, status_code=404)
    if s["busy"]: return JSONResponse({"error": "session is busy"}, status_code=409)
    body = await req.json(); text = (body.get("text") or "").strip()
    if not text: return JSONResponse({"error": "empty"}, status_code=400)
    thinking = body.get("thinking") or s["thinking"]; s["thinking"] = thinking   # list shows the mode actually in use
    q: queue.Queue = queue.Queue(); emit = lambda kind, data: q.put((kind, data))
    emit("status", {"t": f"thinking={thinking}"})
    s["busy"] = True; s["stop"].clear()
    if len(s["turns"]) == 0 and s["title"] in ("new session", f"{s['task']} session"): s["title"] = text[:60]

    def worker():
        turn = {"user": text, "started": datetime.now().isoformat(), "thinking": thinking, "events": []}
        try:
            agent = Agent(s["ex"], thinking=thinking, max_steps=s["max_steps"], max_tokens=int(body.get("max_tokens", 4096 if thinking == "off" else 16384)),
                          on_event=emit, should_stop=s["stop"].is_set, chat_mode=True)
            res = agent.run_turn(s["msgs"], text)
            turn.update({k: v for k, v in res.__dict__.items() if k != "transcript"}); turn["transcript"] = res.transcript
        except Exception as e:
            turn["error"] = f"{type(e).__name__}: {e}"; emit("error", {"message": turn["error"], "trace": traceback.format_exc()[-1200:]})
        s["turns"].append(turn); s["busy"] = False; _sess_save(s); q.put(None)

    threading.Thread(target=worker, daemon=True).start()

    async def gen():
        while True:
            item = await asyncio.to_thread(q.get)
            if item is None: yield sse("end", {}); break
            yield sse(*item)
    return StreamingResponse(gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
