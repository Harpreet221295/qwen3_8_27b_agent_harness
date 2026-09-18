import json, sys, urllib.request, urllib.error

BASE = "http://127.0.0.1:8080"

def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            raw = r.read(); return r.status, r.headers.get("Content-Type"), (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read(); return e.code, e.headers.get("Content-Type"), (json.loads(raw) if raw else None)

def check(cond, msg):
    if not cond: print("FAIL:", msg); sys.exit(1)

s, ct, b = call("GET", "/todos"); check(s == 200 and b == [] and ct == "application/json", f"empty list: {s} {ct} {b}")
s, ct, b = call("POST", "/todos", {"title": "write tests"}); check(s == 201 and b == {"id": 1, "title": "write tests", "done": False}, f"create: {s} {b}")
s, _, b = call("POST", "/todos", {"title": "ship"}); check(s == 201 and b["id"] == 2, f"create 2: {s} {b}")
s, _, b = call("POST", "/todos", {}); check(s == 400 and b == {"error": "title required"}, f"missing title: {s} {b}")
s, _, b = call("POST", "/todos", {"title": ""}); check(s == 400, f"empty title: {s} {b}")
s, _, b = call("GET", "/todos"); check(s == 200 and [t["id"] for t in b] == [1, 2], f"list: {b}")
s, _, b = call("GET", "/todos/2"); check(s == 200 and b["title"] == "ship", f"get: {s} {b}")
s, _, b = call("GET", "/todos/99"); check(s == 404 and b == {"error": "not found"}, f"get missing: {s} {b}")
s, _, b = call("PATCH", "/todos/1", {"done": True}); check(s == 200 and b["done"] is True, f"patch: {s} {b}")
s, _, b = call("PATCH", "/todos/99", {"done": True}); check(s == 404, f"patch missing: {s}")
s, _, b = call("DELETE", "/todos/1"); check(s == 204 and b is None, f"delete: {s} {b}")
s, _, b = call("DELETE", "/todos/1"); check(s == 404, f"delete again: {s}")
s, _, b = call("GET", "/todos"); check([t["id"] for t in b] == [2], f"final list: {b}")
print("ALL OK")
