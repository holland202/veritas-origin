# VEC-003-S1 — prospective hostile-input resource stress addendum

**Status:** REGISTERED_AFTER_VEC003_INITIAL_RESULT / BEFORE_S1_IMPLEMENTATION_AND_EXECUTION / NOT_RUN  
**Date:** 2026-10-11 US Central. **Do not relabel the earlier VEC-003 22/22 registered case result.** That original prospective result and initial harness failure remain recorded in `VEC003_RESULTS.md` (commit `f84294677886eeaf42eefd4dddf5618381c23d4f`).

## New question and scope

Can the **same experimental parser-guarded verifier** return the registered typed outcomes for a repeated mix of hostile but bounded inputs under a **separate Linux process address-space/CPU limit and parent wall-time watchdog**? We measure this narrow case batch, **not** a hard in-process worst-case time/memory guarantee or arbitrary Python object threat.

No change to `vec001.py`, its original tests, or VEC-003 predictions. Ephemeral Ed25519 key; only in-memory fixtures. Pin cryptography 46.0.4, CPython 3.11, Linux x86_64. Record child `ru_maxrss`, child elapsed time, subprocess exit status and exact per-class errors.

## 9 classes x 100 repeats = 900 calls; exact expected outcomes

| Case | Bytes / construction | Expected every call |
|---|---|---|
| H00 | valid signed artifact | BINDING_VERIFIED / BOUND_FINITE_SET_MATCHES |
| H01 | 1,500-deep JSON envelope | REFUSED / MALFORMED_JSON |
| H02 | signed 1,500-deep Statement payload | REFUSED / MALFORMED_JSON |
| H03 | signed 1,500-deep artifact JSON | REFUSED / MALFORMED_JSON |
| H04 | signed flat JSON artifact with 4,097 commas | REFUSED / MALFORMED_JSON |
| H05 | envelope padded to 65,537 bytes | REFUSED / INPUT_TOO_LARGE |
| H06 | signed decoded payload padded to 32,769 bytes | REFUSED / PAYLOAD_TOO_LARGE |
| H07 | signed evidence with 6,000-digit integer | REFUSED / MALFORMED_JSON |
| H08 | valid signed artifact padded to 65,536 bytes | BINDING_VERIFIED / BOUND_FINITE_SET_MATCHES |

**Test requirements:** every response type is `Verification`, never raises; all `execution_authorized` fields are false. Log each class PASS/FAIL and fail immediately on any mismatched result or escaped exception; no retries/resampling. Construct exactly once then reuse bytes 100 times. Fixed deterministic case ordering H00..H08, fresh ephemeral key only per run. Separate watchdog parent process: `resource.RLIMIT_AS=256MiB`, `resource.RLIMIT_CPU=8sec` in child, `subprocess.run(timeout=15)` in parent. No external actions.

## Stop rules

Any mismatch, timeout, nonzero exit or signal is **FAIL**. If OS doesn't provide `resource` or hard limits, report **INCONCLUSIVE** and never claim PASS. If failed, do not tune thresholds or repeat as though preregistered; preserve first outcome and create an explicit amendment. Success remains **visible author-designed stress result**, not independent security validation, scientific truth or cross-platform portability.
