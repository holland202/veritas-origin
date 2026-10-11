# MTA-001 — measured execution and provenance limits

**Status:** `VISIBLE_DEVELOPER_TESTS_PASS / INTERNAL_CONSISTENCY_ONLY / OWNER_REPORTED_EVIDENCE_UNVERIFIED / NOT_SCIENTIFIC_VALIDATION`. Recorded after first instrument execution; registration and predicted cases predate code.

## Baseline and mutation execution

- Preregistration: `research/method_transfer/MTA001_PREREG.md` at commit `67a6283af71acef9ee20b9a47035258a9c3eff56`.
- Typed claims: `CLAIMS.json` at `5ddb211397c2893bdf92b482a98b8b054bc3459b`; auditor code `audit_claims.py` at `3af46299f3355bed440ed1ed8dd694601bee6206`; fixtures `test_mta001.py` at `c70a3822530f5aadf2c9ef10d2ce2f06a5849f8d`. Implementation follows preregistration; original DPC-001 v0.2 checker/spec unchanged.
- GitHub Actions [workflow run 38134616810](https://github.com/holland202/veritas-origin/actions/runs/38134616810), job `114455835304`: **SUCCESS**, shell exit 0. Ubuntu 24.04 x86_64 / CPython 3.11.17. `python -I` used; stdlib-only and no private case sets downloaded.
- Actual audited records printed:
  - `dpc001-v02-blind-run-1 MACHINE_CHECKED`
  - `dpc001-v02-frozen-bytes MACHINE_CHECKED`
  - `dpc001-v02-blind-run-2 DISCLOSED_ONLY`
  - `OVERALL CONSISTENT_WITH_UNVERIFIED machine_checked=2 disclosed_only=1`
- Per-case reconstruction from the **committed** Run 1 JSON: **24 total; 23 PASS, 1 FAIL (T01)**. The result's original `status` is FAIL. The original author-oracle mistake is **not** corrected by this audit, which does not determine whether the expected label was scientifically right.
- Frozen file bytes matched the registered SHA-256 for `SPEC_V02_DRAFT.md` and `checker.py` on the tested branch. This is file integrity against the recorded digest, not proof of independent source authenticity.
- Tests printed `MTA001 VERDICT PASS 11/11`, `FAILED_CASES NONE`. Positive baseline B00 returned exit 0 and the exact `CONSISTENT_WITH_UNVERIFIED` status; deliberate cases N01–N10 returned exit 2 with the preregistered error categories: two `CASE_ROW_CONTRADICTION`, one `RESULT_SUMMARY_DRIFT`, one `CLAIM_DRIFT`, one `SOURCE_DIGEST_DRIFT`, two `PROVENANCE_PROMOTION`, one `MALFORMED_REGISTRY`, one `INVALID_SOURCE_PATH`, and one `INVALID_CLAIM`.
- These negative tests mutate **temporary copies** of actual repository sources. The original evidence bytes remain unchanged.

## Limitations that must not be promoted away

- The auditor and all eleven tests were authored by the same model; a separate GitHub runner is not independently authored analysis or outside review.
- The test is restricted to the typed claims explicitly present in its registry. Unregistered README prose, unstructured interpretation and scientific adequacy are not checked.
- Blind Run 2 remains **OWNER_REPORTED / SEALED / NOT REPRODUCIBLE FROM REPO**. The instrument checks only that the report document exists and the typed registry does not improperly claim independent verification. It cannot compare 24/24 against the unavailable run-2 files or prove that the source statement is true.
- This result is not an independent scientific replication of DPC-001 v0.2 and not an AI safety security validation.
- The Linux enforcement method transfer is entirely prospective documentation. No process sandbox, system-call filter, cgroup rule, vehicle action, permission-gate bypass or deployment occurred.
- Sovereign Veritas remains maintenance-only; **no files in that repository were changed**.
- Source Git blob SHA-1 values in `TRANSFER_MAP.md` are version references to primary documents, not a new source SHA-256 archive.

**Disposition:** keep PR #34 in draft for external methodological review. Future public reports can encode their machine-assertable numbers in an explicit registry while preserving human prose separately, borrowing the method rather than copying GuitarPedal code. Use a separate experimental preregistration to extend to additional actual measurement artifacts.
