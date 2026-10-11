# MTA-001 — Source-method assimilation and claim-drift audit preregistration

**Registered before implementation:** 2026-10-11 (US Central). **Status: PLAN_ONLY / NO_NEW_RUN / NOT_VALIDATED.**
**Location:** separate experimental research branch based on Veritas-Origin `main` at merge `19efdc5fc7a0f2c90226a836e0cc9163e4692b3c`. Do not modify frozen DPC-001 v0.2 checker/specification. Do not alter, unseal or rerun the private Blind Run 2 evidence. Do not add active features to **Sovereign Veritas**, whose `STATUS.md` explicitly states maintenance-only.

## Origin of transferred method

- GuitarPedal README Git blob `72760ca1a08c9664c66ca9fb91a5c6344565c97b`: the host bench compiles the **same signal-processing implementation**, not an approximate second implementation; remeasurement is a separate check from hardware integration. `Validation/bench/bench.c` blob `f8034440bce63c4f828f7872c51b6cbdded34228`.
- GuitarPedal `scripts/check-readme.py` Git blob `02e5ed4942694cd84970be8e0f9cd46dac311091`: warns on drift between written list and source-effect names; explicitly does not verify prose.
- GuitarPedal `Validation/check-analysis.py` Git blob `a627d21c8a51eb168abda3f066dac6c1e3c606cd`: remeasures deterministic test-bench outputs and compares written numeric values with their stated rounding precision; separately warns and does not claim truth of prose.
- Git repo snapshot: `torvalds/GuitarPedal` `main` at `ab3b7743dcd2a8931c6ba79cbb11a643fcc57be8`. No endorsement, contribution or permission from upstream implied; adapt **method**, not code.
- Linux `master` source snapshot `a5ebb76233b79db01e82e061173cb73c6d2b5c6b`: seccomp docs blob `cff0fa7f3175e4d2482aafd0ad4ed3b7045a437a`, Landlock docs blob `84cb7bf6b3ed627a3e2ca1f168f1e23b08efbcf9`, cgroup v2 docs blob `86a2a0099178ea37b22346e49d5b597652220f1b`. Separate design transfer only; no kernel/user process confinement installed.

These Git blob IDs are SHA-1 identifiers, **not SHA-256 source manifests**. This record is a read-only inspected-source map; a later full source-materialization audit is needed for reproducible external source hashing.

## Research hypothesis MTA-001 (narrow)

An explicit typed **claim registry** and a read-only stdlib instrument can detect drift between a reported DPC-001 Blind Run 1 outcome and the actual **24 committed per-case observations**, and between a frozen-file digest assertion and the repository bytes. It must NOT silently elevate Blind Run 2, whose evidence is sealed and not present here, into an independently verified result.

### Input and output contract

`audit_claims.py --root <repository_root> --registry <typed_json_file>` with no network and no mutations. Registry specifies:

1. `case_result` for the repository's `coordination/dpc001_v02/blind_run_1/evidence/blind_run_v1.json`: expected `total:24`, `passed:23`, `failed:1`, `status:"FAIL"`, `failed_case_ids:["T01"]`.
2. `byte_digest` for frozen `coordination/dpc001_v02/SPEC_V02_DRAFT.md` SHA256 `fce85463ebbb552b0bf44a4a9bb90d5851101b378d31f91a6bb7786405737186` and `coordination/dpc001_v02/checker.py` SHA256 `f2746a43e1e7360f645be912e552a84e53eca950d07d93d98adbc4d087eeca34`.
3. `reported_only` for Blind Run 2, with `status: "OWNER_REPORTED"`, `independent_verification: false`, `raw_evidence_present: false`. That record remains **DISCLOSED_ONLY**, never MACHINE_CHECKED. Its reported count (24/24) is not independently recomputed or proven by this instrument.

For an internally consistent source set, expected overall audit `CONSISTENT_WITH_UNVERIFIED`, **never** `SCIENTIFICALLY_VALIDATED`; exit 0 means only defined machine-checkable assertions consistent, one unverified claim held unpromoted. For a drift, invalid source/registry, or incorrect provenance promotion, exit nonzero with a stable reason and case ID. The registry is **not** a scientific oracle and results establish no model correctness.

### Prospective test matrix (before code)

| ID | Input variation | Required outcome |
|---|---|---|
| B00 | pristine repository data and registry | exit 0, 2 MACHINE_CHECKED, 1 DISCLOSED_ONLY; overall CONSISTENT_WITH_UNVERIFIED |
| N01 | per-case actual_primary changed but status left PASS | nonzero, CASE_ROW_CONTRADICTION |
| N02 | per-case status changed from FAIL to PASS without matching observations | nonzero, CASE_ROW_CONTRADICTION |
| N03 | result summary headline `status` changed FAIL→PASS | nonzero, RESULT_SUMMARY_DRIFT |
| N04 | registry `passed` changed 23→24 | nonzero, CLAIM_DRIFT |
| N05 | frozen `checker.py` one byte changed | nonzero, SOURCE_DIGEST_DRIFT |
| N06 | reported-only record falsely claims independent verification true | nonzero, PROVENANCE_PROMOTION |
| N07 | reported-only claim substitutes non-existent raw evidence as verified | nonzero, PROVENANCE_PROMOTION |
| N08 | registry includes duplicate JSON keys | nonzero, MALFORMED_REGISTRY |
| N09 | registry source path escapes repository root | nonzero, INVALID_SOURCE_PATH |
| N10 | expected case count 0 (anti-vacuity) | nonzero, INVALID_CLAIM |

Additional exploratory tests can be added only after their status is marked `POST_REGISTERED`. Exit 0 cannot imply scientific truth, independent validation, every README sentence is accurate, or that sealed inputs have been examined.

## Intentional design distinctions

- Unlike prose phrase matching, compare **typed fields with primary source JSON**. Do not infer truth from “PASS” as a string; independently count per-case statuses and check each actual/expected label and issue set.
- A published result can be internally consistent but still empirically wrong or author-biased.
- There is no general semantic parser for every statement in prose: the audit covers **only explicitly registered assertions**. A stale sentence outside the registry remains potentially undetected.
- Keep author-designed tests and external review separate, keep all negative findings, require explicit version/byte bindings. Run1 remains FAIL 23/24 even if later tests improve. Frozen DPC-001 remains frozen.
