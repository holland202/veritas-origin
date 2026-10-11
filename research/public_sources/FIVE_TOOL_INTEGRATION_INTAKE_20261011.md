# Five-tool research integration intake — 2026-10-11

Status: DESIGN INTAKE ONLY / UNVALIDATED / NO DEPENDENCIES INSTALLED / NO EXECUTION AUTHORIZED.

Scope: experimental Veritas-Origin research. No modifications to frozen DPC-001 files or Sovereign Veritas main. Upstream repository names are leads, not independently authenticated supply-chain artifacts. Pin exact upstream commits, license and file hashes before importing code.

## Candidates and staged implementations

1. Hypothesis — https://github.com/HypothesisWorks/hypothesis (master at intake). Build an **optional** property-based test harness for malformed contracts, unknown keys, normalization collisions, inconsistent provenance and replay invariants. Start with generated data against an isolated fixture, not the frozen checker. Compare seeded failures to hand-written controls; retain shrinking seeds and reproductions.
2. Atheris — https://github.com/google/atheris (master at intake). Build a disposable parser-only fuzz target with strict iteration/time/memory budgets and crash corpus retention. Verify Python 3.14 and Android/aarch64 support before attempting Termux installation. Prefer a disposable Linux environment initially. No network targets.
3. Inspect AI — https://github.com/UKGovernmentBEIS/inspect_ai (main at intake). Draft a separate LDE evaluation adapter: explicit dataset revision, task IDs, model/runtime revision, scoring schema, attempt budget, hidden untouched holdout, and failed-run provenance. Do not modify or reclassify prior LDE results.
4. Termux API — https://github.com/termux/termux-api (master at intake). Extend TSP-001 in a **new experimental module**, initially passive: distinguish COMMAND_FOUND, PERMISSION_VERIFIED, API_RESPONSE_VALIDATED, and UNKNOWN. Battery/sensor access only with explicit user permission. Never infer broker confinement or authorize execution from local observations.
5. OSS-Fuzz — https://github.com/google/oss-fuzz (master at intake). Assimilate corpus curation, deterministic reproducer, crash deduplication, regression and provenance patterns. Do not onboard a project to hosted fuzzing or transmit artifacts without separate consent.

## Cross-cutting source manifest fields

Record: upstream URL; immutable commit SHA; file path; SHA-256; license and obligations; retrieval timestamp UTC; retrieval mechanism; access status; review status; execution environment; dependency lock hash; command; exit code; stdout/stderr digests; negative findings; reviewer; evidence boundary. UNKNOWN is not PASS.

## Acceptance gates

A. Freeze baseline hashes and tests; record reproducible baseline outputs.
B. Preregister positive and negative controls, including an intentionally broken target and an inert target.
C. No import of third-party executable code until license/dependency review and pinned revisions.
D. No outbound scan, exploit, remote service, background job, privileged Android action or external data submission.
E. Run on a disposable branch/environment; preserve exit codes and artifacts. Failures and incomplete runs remain visible.
F. Independent verification required before claiming robustness, portability, containment, or security.

## Proposed order

Phase 1: manifest and Hypothesis harness.
Phase 2: bounded Atheris fuzzing and OSS-Fuzz-style corpus process.
Phase 3: LDE Inspect AI evaluation prototype.
Phase 4: permission-gated Termux API probe extension.

This document does not claim any test was executed or any tool integrated.
