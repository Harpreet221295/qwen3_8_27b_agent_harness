`/app/server.py` is a small HTTP JSON API using only the Python standard library (`http.server`). It has several
bugs. `/app/spec.md` describes the intended behaviour and `/app/client_check.py` exercises it against a running
server. Start the server in the background (e.g. `python server.py &`, it listens on port 8080), run the checker,
fix the bugs until `python client_check.py` prints `ALL OK`, then stop the server. Do not change `client_check.py`.
