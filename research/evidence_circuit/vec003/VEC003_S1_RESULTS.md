# VEC-003-S1 — hostile-input process-budget stress result

**State:** `VISIBLE_AUTHOR_STRESS_PASS / NOT_INDEPENDENTLY_AUDITED / NO_PRODUCTION_PROMOTION`. This is a separate **post-VEC003-results preregistration** at `7eebdadfd547b8f43f90320d30c80bc90df84f54`, not a new interpretation of the initial VEC-003 22/22 outcomes.

## Executed registered S1 matrix

- **Workflow:** [38131916373](https://github.com/holland202/veritas-origin/actions/runs/38131916373), job `114447826391`.
- **Observed:** GitHub job success; program printed `VEC003_S1_CHILD_EXIT 0`, `S1_CLASS_PASS H00..H08 100/100`, `VEC003_S1_PASS 900/900`, `VEC003_S1_VERDICT PASS`; no retries or prediction changes.
- **Environment:** Ubuntu 24.04 GitHub runner, CPython 3.11.17 x86_64, cryptography 46.0.4, ephemeral Ed25519 keys, fully in-memory fixtures.
- **Resource limits in child:** `RLIMIT_AS = 256 MiB`, `RLIMIT_CPU = 8 seconds`; parent watchdog `subprocess.run(timeout=15)`. If the child exceeded these hard limits, its run would not return the required exit 0 + PASS marker.
- **Observed metrics from inner 900-call loop:** `elapsed_inner_ms=949.07`, `peak_rss_kib=27616`. Time excludes Python interpreter startup, package imports and fixture generation; peak RSS includes child process to point of measurement. These numbers are not service-level performance guarantees.
- **Input mix:** H00 positive valid signature; H01–H03 1500-depth unsigned envelope/signed payload/signed artifact; H04 signed artifact with 4097 commas; H05 envelope 65537 bytes; H06 signed payload 32769 decoded bytes; H07 signed 6000-digit numeric evidence; H08 valid signed artifact 65536 bytes. Each of nine cases executed 100 times with matching typed outcomes and `execution_authorized=false`.

## Concurrent regressions

Following the S1 workflow commit `922dd075bfa01611da298ab3a09604f9c1a7cdb8`, GitHub workflows on the same head reported:
- [38131916367](https://github.com/holland202/veritas-origin/actions/runs/38131916367) original VEC-001 fixtures **SUCCESS**;
- [38131916390](https://github.com/holland202/veritas-origin/actions/runs/38131916390) original 21 and VEC-002-R1 15 repair fixtures **SUCCESS**;
- [38131916372](https://github.com/holland202/veritas-origin/actions/runs/38131916372) VEC-003 baseline 22/22 **SUCCESS**.

## Epistemic and security limitations

Tests, implementation, and interpretation have the **same model author**; CI on a separate cloud substrate is not independent review. Adversarial classes were selected by the author and are not a statistically representative distribution. Tests do not cover arbitrary nested object types supplied through `Mapping`, compromised trusted keys/context, special Python-level exceptions, host process-control bypass, scientifically false but correctly signed claims, real action authorization or other platforms. The child RLIMIT strategy must be enforced by a trusted host before accepting untrusted inputs; embedding the pure-Python verifier without the host supplies no hard memory/CPU bound. The 900 calls are sequential under one ephemeral signer/context, with no concurrency or long-duration retention test.

## Disposition

**HOLD PRODUCTION MERGE.** The preregistered S1 outcomes are supported on the recorded platform and branch, but an independent reviewer, cross-parser conformance tests, resource-exhaustion discovery outside the authored cases, and deployment-level gate testing are still required. Preserve VEC-002's original S1 failure and its subsequent R1/VEC-003 repairs as distinct, time-ordered facts.
