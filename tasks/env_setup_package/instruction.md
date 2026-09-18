`/app/run_analysis.py` fails because a dependency is missing. The internet is NOT available.
The needed package `mathx` is vendored as source under `/app/vendor/mathx/`. Install it (for example with
`pip install /app/vendor/mathx`) or otherwise make it importable system-wide, then run the script so it
produces `/app/output.txt`. Also fix anything else that stops the script from running.
