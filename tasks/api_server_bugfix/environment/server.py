import json
from http.server import BaseHTTPRequestHandler, HTTPServer

TODOS = {}
NEXT_ID = 1


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body=None):
        self.send_response(code)
        if body is not None:
            data = json.dumps(body).encode()
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            self.end_headers()

    def _body(self):
        n = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(n)) if n else {}

    def _todo_id(self):
        parts = self.path.strip("/").split("/")
        if len(parts) == 2 and parts[0] == "todos":
            return int(parts[1])
        return None

    def do_GET(self):
        if self.path == "/todos":
            return self._send(200, TODOS.values())
        tid = self._todo_id()
        if tid in TODOS:
            return self._send(200, TODOS[tid])
        self._send(404, {"error": "not found"})

    def do_POST(self):
        global NEXT_ID
        body = self._body()
        title = body.get("title")
        if title is None:
            return self._send(400, {"error": "title required"})
        todo = {"id": NEXT_ID, "title": title, "done": False}
        TODOS[NEXT_ID] = todo
        self._send(200, todo)

    def do_PATCH(self):
        tid = self._todo_id()
        if tid not in TODOS:
            return self._send(404, {"error": "not found"})
        TODOS[tid]["done"] = self._body().get("done")
        self._send(200, TODOS[tid])

    def do_DELETE(self):
        tid = self._todo_id()
        if tid not in TODOS:
            return self._send(404, {"error": "not found"})
        del TODOS[tid]
        self._send(204, {})

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
