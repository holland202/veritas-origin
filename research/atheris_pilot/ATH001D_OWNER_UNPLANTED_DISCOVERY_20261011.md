# ATH-001D — unplanted deterministic random mutant detection (2026-10-11)

Status: OWNER-REPORTED EXECUTION; NOT INDEPENDENTLY REPRODUCED. Termux Python 3.14.6 on Android ARM64. Engine: Python standard library `random.Random`, NOT Atheris and NOT coverage-guided fuzzing.

## Procedure
Seed `20261011`; up to 10,000 iterations. Each iteration chooses `n = rng.randrange(33)` then `data = rng.randbytes(n)`. Reference: `len(b)>=2 and b[:2]==b'OK'`; known-bad mutant: `len(b)>=2 and b[:1]==b'O'`. Stop at first divergent output. No deliberately planted input in this trial. An earlier attempt was NOT EXECUTED due to terminal paste starting `- <<'PY'` rather than `python - <<'PY'`; the later complete command ran successfully.

## Owner-reported output
`EXPERIMENT=ATH-001D`, `PLANTED_INPUT=NO`, `TESTED=489`, `MUTANT_DETECTED=True`, `HEX=4fec1c523f7e4b58f5c83c5783881c5c19e87dbe7b49`, `SHA256=5ed6dc194a9dae6085f86c2fb9c87ba4fee53d811f7bb4af15b53ab88cdb7384`, `REFERENCE=False`, `MUTANT=True`.

## Claim boundary
Generated-input detection of a known injected defect within this single deterministic seeded run. Not discovery of an unknown defect, not a statistical detection-rate estimate, not an Atheris compatibility or coverage result, and not independent verification. Counterexample and seed reported in chat; no independently captured full run log. Next: minimize counterexample with preserved mismatch predicate and rerun verification.
