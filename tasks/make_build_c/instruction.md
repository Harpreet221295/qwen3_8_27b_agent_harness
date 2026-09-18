`/app` contains a small C project (`main.c`, `mathlib.c`, `mathlib.h`, `Makefile`). `make` currently fails.
Fix whatever is wrong (in the Makefile and/or the sources) so that:

- `make` builds an executable `/app/calc` with no warnings under `-Wall -Werror`
- `./calc 6 7` prints `42`
- `./calc 10 0` prints `error: division by zero` to stderr and exits with code 2 when run as `./calc -d 10 0`
  (the `-d` flag selects division; default is multiplication; `./calc -d 10 4` prints `2.5`)
- `make clean` removes the binary and object files
