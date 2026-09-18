Create a command-line tool `/app/wc.py` that mimics a subset of `wc`:

- `python wc.py FILE...` prints, for each file, `LINES WORDS CHARS FILENAME` separated by single spaces.
- Flags `-l`, `-w`, `-c` restrict output to only lines, words, or chars respectively (combinable, always in the order lines, words, chars).
- With more than one file, print a final line `... total`.
- A missing file prints `wc.py: NAME: No such file` to stderr and the program exits with code 1 after processing the others.

Sample files are in /app/samples/. Verify your tool against the real `wc` output.
