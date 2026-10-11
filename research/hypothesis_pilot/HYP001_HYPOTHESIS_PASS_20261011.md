# HYP-001 Termux Hypothesis run — owner-provided evidence (2026-10-11)

Research Director, Orchestrator, and Project Owner: Chad Holland.

## Scope and evidence class
OWNER-REPORTED DEVICE EXECUTION. Terminal transcript provided by owner; not independently executed by ChatGPT. Target: Samsung S25 Ultra / Android Termux / Python 3.14.6. Isolated venv: `$HOME/venvs/hyp001`. Source: `$HOME/test_hyp001.py` extracted from branch `research/five-tool-intake-20261011`; earlier owner-reported SHA-256 `eb95e9159ad9d248c9f4e577166783658d7f66111d97fea9e13a6e5d062fa09b`.

## Dependencies
- Hypothesis 6.155.7, MPL-2.0, installed in venv
- sortedcontainers 2.4.0, Apache-2.0, installed in venv
- `pip install --only-binary=:all: hypothesis sortedcontainers` reported requirements satisfied and exit code 0; user reported successful initial installation.
- No installation into system Python was reported.

## Observed tests
- `$HOME/venvs/hyp001/bin/python -I $HOME/test_hyp001.py`: `Ran 6 tests in 1.241s`, `OK`, `TEST_EXIT_CODE=0`.
- Second run: `Ran 6 tests in 0.227s`, `OK`, `TEST_EXIT_CODE=0`.
- Four standard-library tests and two optional Hypothesis-generated property tests (as designed in experimental toy harness). Passing assertions do not demonstrate that all generated cases or mutations were independently audited.

## Negative evidence retained
An earlier default pip install attempted a maturin Rust build, failing in clap 4.6.1 because `examples/demo.md` was absent. `cargo` exited 101 and Hypothesis remained uninstalled. The wheel-only path subsequently succeeded. This does not establish why the missing Rust source occurred.

## Other device context
Owner screenshot: Shizuku v13.5 running via adb; **0 authorized applications**. No Shizuku authorization or elevated command executed. Owner reports Black Shark cooling fan attached. Neither is evidence of thermal performance or security enforcement.

## Claim status
HYP-001 EXPERIMENTAL HARNESS PASS (OWNER-REPORTED; TWO RUNS); frozen DPC checker untouched; independent validation and production applicability NOT ESTABLISHED. No claim that Shizuku changes security properties.
