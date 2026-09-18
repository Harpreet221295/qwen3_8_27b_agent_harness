Running `python /app/parse_config.py /app/configs/prod.ini` crashes with a traceback. Investigate and fix
`parse_config.py` so that it works for every file in `/app/configs/` (run it on each one).

Expected behaviour: print one line per section as `[section] key1=value1 key2=value2 ...` with keys in the order
they appear, values with surrounding whitespace stripped, `#` and `;` comment lines ignored, blank values allowed
(printed as `key=`), and duplicate keys in a section: last one wins. A file with no sections prints nothing and exits 0.
