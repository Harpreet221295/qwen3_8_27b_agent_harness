# Todo API spec (port 8080)
- `GET /todos` → 200, JSON list of todos `[{"id": int, "title": str, "done": bool}, ...]`
- `POST /todos` with body `{"title": str}` → 201, the created todo (ids start at 1 and increment). Missing/empty title → 400 `{"error": "title required"}`
- `GET /todos/<id>` → 200 todo, or 404 `{"error": "not found"}`
- `PATCH /todos/<id>` with `{"done": bool}` → 200 updated todo, 404 if missing
- `DELETE /todos/<id>` → 204 empty body, 404 if missing
- All responses have `Content-Type: application/json` (except 204).
