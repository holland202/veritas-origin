# ATH-001C — planted positive control (2026-10-11)

Status: OWNER-REPORTED EXECUTION, NOT INDEPENDENTLY REPRODUCED. Python standard library, Termux Python 3.14.6, Android ARM64. This is not native Atheris fuzzing.

Reference: returns true iff byte input length >= 2 and first two bytes are `OK`. Known-bad mutant: returns true iff length >= 2 and first byte is `O`. RNG seed `20261011`, budget 10,000 inputs, but input zero explicitly planted as `b'OX'`.

Observed owner output: `TESTED=1`, `MUTANT_DETECTED=True`, `COUNTEREXAMPLE_HEX=4f58`, `COUNTEREXAMPLE_SHA256=1b07fa6882367e4579831f9d91b827e3bbb1c77552a914f11fd4051a2cfb4d1b`, `REFERENCE=False`, `MUTANT=True`.

Interpretation: detection mechanism passed its planted positive control. No independent discovery, coverage-guided fuzzing, random-discovery rate, or security robustness demonstrated. Preserve this control separate from any later unplanted discovery experiment.
