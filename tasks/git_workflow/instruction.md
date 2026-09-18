/app is a git repository with some uncommitted work. Do the following, in this order:

1. The file `notes.tmp` should never be committed: add it to `.gitignore` (commit the `.gitignore` change on `main` with message `Ignore temp files`).
2. Create a branch `feature/greeting` from `main`.
3. On that branch, add a function `greet(name)` to `app.py` that returns `"Hello, <name>!"`, and commit it with message `Add greeting function`.
4. Merge `feature/greeting` back into `main` (a fast-forward is fine).
5. Tag the resulting `main` commit as `v0.1.0`.

Leave the working tree clean at the end. Do not delete the `feature/greeting` branch.
