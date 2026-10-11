# ATH-001 — Termux Atheris packaging preflight (2026-10-11)

Owner-reported device execution; not independently reproduced. Samsung S25 Ultra, Termux Python 3.14.6, `sys.platform=android`, aarch64, SOABI `cpython-314-aarch64-linux-android`. `atheris` not installed. `pip config list` showed only `global.disable-pip-version-check='true'` (no custom index shown). `pip index versions atheris` listed 3.0.0 as highest visible version, through 1.0.0.

## Negative probes
- `python -m pip download --only-binary=:all: --no-deps --dest "$HOME/tsp002-evidence" 'atheris==3.1.0'`: `No matching distribution found`, numeric exit code not reliably captured.
- `python -m pip download --no-deps --no-binary=:all: --no-build-isolation --dest "$HOME/tsp002-evidence" 'atheris==3.1.0'`: `No matching distribution found`, `DOWNLOAD_EXIT_CODE=1`. The first attempt at this command was accidentally concatenated into an echo and did not execute; a later standalone attempt did execute.
- `python -m pip download --only-binary=:all: --no-deps --dest "$HOME/tsp002-evidence" 'atheris==3.0.0'`: `No matching distribution found`, `WHEEL_PROBE_EXIT_CODE=1`.

## Claim boundary
No compatible wheel found by configured pip for the requested version and platform. Does not prove Android source build impossible, or that upstream releases do not exist. No native Atheris installed or executed. Native installation DEFERRED. Next: isolated stdlib toy parser fuzz controls, no changes to frozen DPC files. The exact raw pip logs and package index state were not independently archived; commands/output supplied by owner in chat.
