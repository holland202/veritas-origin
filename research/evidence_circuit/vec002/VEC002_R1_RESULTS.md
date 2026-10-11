# VEC-002-R1 — post-finding repair results (append-only)

**Status:** `LOCAL_REPAIR_SELFTEST_PASS / HISTORICAL_S1_FAIL_PRESERVED / NOT_INDEPENDENTLY_VALIDATED / NO_PRODUCTION_PROMOTION`
**Repair preregistration** before candidate patch: `VEC002_R1_PREREG.md` at `37af08c8d878f602ba0866c5fb6be1382bab9fc7`.
**Candidate implementation:** change in `vec001._json`: map Python JSON parser `RecursionError` to `Rejection("MALFORMED_JSON")` (commit `b5ec250056ffba57dcfaa732b7098cfed831eecd`); all other VEC-001 code untouched.

## Three separate observed runs after repair

| Execution | GitHub Actions run | Job | Observed | Interpretation |
|---|---|---|---|---|
| R1 new 15-case post-finding matrix | [38109756175](https://github.com/holland202/veritas-origin/actions/runs/38109756175) | `114382684874` | `VERDICT PASS matching=15/15`, exit 0 | Narrow author-designed fix demonstrated on visible cases |
| VEC-001 original 21-case regression | [38109756175](https://github.com/holland202/veritas-origin/actions/runs/38109756175) | `114382684820` | `VERDICT PASS matched 21/21`, exit 0 | Original visible behavior preserved |
| VEC-002 original prediction matrix *against repaired code* | [38109756181](https://github.com/holland202/veritas-origin/actions/runs/38109756181) | `114382684716` | `PREDICTIONS 12/15`; `S1_TYPED_REFUSAL_FAIL_CASES NONE`; `PREDICTION_MISMATCH_CASES A01,A02,A03`; exit 1 | **Expected historical prediction mismatch**, not a new S1 safety failure |

All on Ubuntu 24.04 / CPython 3.11.17 x86_64 / cryptography==46.0.4 with ephemeral test keys. The three changed cases were:
- A01 bounded unsigned deep envelope: before `CRASH:RecursionError`, after `REFUSED/MALFORMED_JSON`.
- A02 bounded correctly signed deep Statement payload: before `CRASH:RecursionError`, after `REFUSED/MALFORMED_JSON`.
- A03 bounded correctly signed deep artifact: before `CRASH:RecursionError`, after `REFUSED/MALFORMED_JSON`.

The original VEC-002 failing run [38109650930](https://github.com/holland202/veritas-origin/actions/runs/38109650930), `VEC002_ORIGINAL_FINDINGS.md` and its original predictive classifications remain unchanged in the experimental base branch. A post-finding fix cannot retroactively make that negative result PASS.

## Remaining gaps

- Depth tests at 1,500 levels demonstrate only these inputs; no claim about all bounded inputs or memory/CPU denial-of-service safety.
- Not externally authored, independently audited, or cross-implementation reproduced.
- No replay protection, cross-evidence reconciliation, signer revocation, anti-rollback ledger or reliable real-world truth check.
- VEC-001 still returns no execution authorization. No external execution interface was tested.
- No change to frozen DPC-001 v0.2.

**Decision:** retain R1 as an experimental repair candidate, not a validated production patch. Review parser resource bounds and broader adversarial input shape generation before merging up the experimental stack.
