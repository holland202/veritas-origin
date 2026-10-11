# DPC-001-M1: Pre-seal error interception (methodological finding)

```yaml
finding: DPC-001-M1
type: METHODOLOGICAL (about the evaluation process, not about the checker)
status: OBSERVED_ONCE / NOT_GENERALIZED
recorded_by: Claude (Opus 5.5) from owner-run outputs; named by ChatGPT; Chad directed, 2026-10-09
```

## Claim
After blind run 1 failed because of a test-author error, a pre-seal integrity gate was built from that failure. On its first real use it caught a test-author error of the same class **before sealing**, so blind run 2 was not affected by it.

## Evidence (all pasted; owner-run unless stated)

| | Blind run 1 | Blind run 2 |
|---|---|---|
| Test-author mistake | T01: oracle expected `SCHEMA_INVALID`, contract carried the valid schema | T03: oracle expected `STUDY_ID_MISSING`, contract carried a study_id |
| Detected | after execution, by post-run unsealing (PR #25 note 029) | before sealing, by `preseal_gate.py` |
| Gate output | (gate did not exist; applied afterwards: `PRESEAL_GATE FAIL` on G3 + G4, note 030) | `FAIL  G4 T03: oracle requires STUDY_ID_MISSING but study_id is present` / `PRESEAL_GATE FAIL (1 fail, 0 warn, 24 cases)` |
| Corrected set | not applicable | `PRESEAL_GATE PASS (0 fail, 0 warn, 24 cases)` |
| Evaluation outcome | **FAIL 23/24** (kept) | **PASS 24/24** |

- Gate used for run 2 = gate in the repo at `45ccccc`: sha256 `c407364c990ef819e6ca8937d4395d3f4bc6d36bef8ac25210776d02bf24cdd6` (owner recomputed both copies).
- The failed run-2 draft (`cases_preseal_failed.json`) is kept in the owner's private run-2 folder.
- Gate self-test: 9 of 9, Claude-run and owner-reproduced (notes 033, 034).

## Mechanism
Check G4 compares each expected reason code with a precondition visible in the case itself (for example `STUDY_ID_MISSING` requires an absent or blank `study_id`). It reads only the cases and the answer key and never runs the checker, so it can be used on a sealed set without breaking blindness.

## Limits
1. **One observation.** One error caught, in one run. No rate of interception is claimed.
2. **One error class.** G4 covers four reason codes, and G3 covers duplicate cases. It does not detect an expected label that is wrong under the spec.
3. **Deterministic software, not learning.** The improvement came from the research process (failure → control → test of the control → reuse), not from any AI system improving itself.
4. **Not validation of the checker.** M1 is about catching test errors. It adds nothing to whether DPC-001 v0.2 is correct beyond the two blind-run results.
