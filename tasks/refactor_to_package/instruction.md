`/app/monolith.py` contains three groups of functions: string helpers, math helpers, and file helpers.
Refactor it into a package `/app/utils/` with modules `strings.py`, `maths.py`, `files.py` and an
`__init__.py` that re-exports every public function, so both of these keep working:

```python
from utils import slugify, clamp, read_lines          # via __init__
from utils.strings import slugify                     # via submodule
```

Behaviour must not change. Delete `monolith.py` when done. The existing tests in `test_monolith.py` import
from `monolith`; update that import line to `from utils import *` (that is the only change allowed in the test file) and make sure `pytest` passes.
