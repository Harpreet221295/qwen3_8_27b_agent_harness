`/app/access.log` is a web server log in the common format `IP - - [timestamp] "METHOD /path HTTP/1.1" STATUS BYTES`.

Produce:
1. `/app/top_ips.txt` — the 5 IPs with the most requests, one per line as `COUNT IP`, highest first (ties broken by IP ascending).
2. `/app/errors.txt` — every request path that returned a 5xx status, sorted, unique, one per line.
3. `/app/summary.txt` — a single line `total=<N> errors=<M> unique_ips=<K>` where errors counts 4xx+5xx responses.

Use shell tools (grep/awk/sort/uniq) or Python — your choice.
