# ATH-001E — deletion minimization of ATH-001D counterexample

Status: OWNER-REPORTED EXECUTION on Termux Python 3.14.6, Android ARM64; not independently reproduced. Python standard library only; Atheris not installed or executed.

## Input and method
Original generated-input counterexample: `4fec1c523f7e4b58f5c83c5783881c5c19e87dbe7b49` (22 bytes), as reported for ATH-001D. Reference accepts iff length >= 2 and first two bytes equal `OK`; known-bad mutant accepts iff length >= 2 and first byte equals `O`. Predicate: `reference(data) != mutant(data)`. Owner executed iterative single-byte deletion, restarting after each successful removal.

## Observed output
- `EXPERIMENT=ATH-001E`
- `ORIGINAL_LENGTH=22`
- `MINIMIZED_LENGTH=2`
- `MINIMIZED_HEX=4f49` (`OI`)
- `MINIMIZED_SHA256=f6ddf237cd4dec7fd3140ed809a4edda8ac44fd31d58a479ee20301532438764`
- `MISMATCH_PRESERVED=True`
- `REFERENCE=False`; `MUTANT=True`

## Interpretation and limitations
20 of 22 bytes removed (90.91% reduction). This example is globally minimum by byte length for the stated predicate because both functions return False on lengths < 2. That logical proof relies on the stated source definitions, not an independent runtime validation. The exact minimized bytes are one of many length-2 counterexamples. No Atheris fuzzing, production authorization security claim, or independent reproduction established. Preserve the owner-reported result and original seed/hex; no changes to frozen DPC artifacts.
