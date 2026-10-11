# VEC-002 — adversarial boundary experiment, prospective registration

**State:** REGISTERED_BEFORE_IMPLEMENTATION_AND_RUN / VERIFIER_UNCHANGED / NOT_RUN
**Date:** 2026-10-10 America/Chicago
**Author:** GPT-6. **Target:** `research/evidence_circuit/vec001.py` at PR #30 commit `cb733f9216d5aebdeabed01ba203c6b52a2b0c66`, Git blob SHA `b328a241c498941af8807954050a0ca6af959010`. Dependency `cryptography==46.0.4` and CPython 3.11 in GitHub Actions.
**Boundary:** local/in-memory tests using ephemeral Ed25519 keys; no external actions, hardware, user files or other repositories modified. Frozen DPC-001 v0.2 remains untouched.

## Question

Does the bounded, offline VEC-001 verifier (a) always return a typed refusal rather than throw an unhandled exception on malformed bounded hostile bytes, (b) reject tampered or wrongly rooted evidence, and (c) distinguish byte authenticity from replay protection and contradictory signed sources?

## Independent scoring axes

- **Safety invariant S1**: every call to `verify` returns a `Verification` instance without throwing; on any invalid input `binding_status == REFUSED` and `execution_authorized == false`. A crash is **FAIL** for S1 *even if predicted*; crashes cannot be presented as security success.
- **Prediction match P1**: record observed output class `BINDING_VERIFIED`, `REFUSED`, or `CRASH:<exception class>`; compare to predeclared prediction. Matching a predicted crash supports fault localization, **not** S1.
- **Scope outcome S2**: independent signed bundles with the same study/claim can be individually authentic yet conflict; accepted replay or conflict is a **known missing system-layer protection**, *not* a claim the individual VEC-001 verifier violated its narrow preregistered specification.
- **Anti-vacuity**: a legitimate signature must continue to pass, and all results must keep `execution_authorized=false`.

## Predeclared cases / predicted observations

| Case | Input | Prediction | S1 expected |
|---|---|---|---|
| C00 | valid signed statement + valid finite-list artifact | BINDING_VERIFIED | PASS |
| A01 | a ~1,500-level deeply nested **unsigned envelope JSON** inside 64 KiB | CRASH:RecursionError | FAIL (must instead REFUSE) |
| A02 | correctly signed DSSE envelope whose **payload** is a ~1,500-level nested array (under payload cap) | CRASH:RecursionError | FAIL (must instead REFUSE) |
| A03 | correctly signed subject digest + DSSE envelope for ~1,500-level **artifact JSON** | CRASH:RecursionError | FAIL (must instead REFUSE) |
| A04 | authenticated payload but untrusted key ID | REFUSED | PASS |
| A05 | signer removed from trust map | REFUSED | PASS |
| A06 | signed valid-shaped artifact with duplicate nested JSON key | REFUSED | PASS |
| A07 | correctly signed artifact with nonfinite literal `NaN` | REFUSED | PASS |
| A08 | correctly signed evidence with `1e309` as contrast value | REFUSED | PASS |
| A09 | same valid signed evidence verified twice at same trusted timestamp | BINDING_VERIFIED twice | PASS for VEC-001; replay defense ABSENT |
| A10 | two individually signed, internally valid, mutually contradictory finite-contrast lists for same study and claim, verified separately | BINDING_VERIFIED twice | PASS for VEC-001; conflict defense ABSENT |
| A11 | otherwise valid evidence with expired trusted timestamp | REFUSED | PASS |
| A12 | valid evidence with two envelope signature entries | REFUSED | PASS |

## Construction constraints

Use the committed `test_vec001` fixture helpers for base context and local ephemeral signing; generate hostile bytes in memory. For A01/A02/A03 build bounded repeated arrays as raw bytes, **not** via Python recursive serialization. A02 signs the exact hostile payload bytes by DSSE PAE. A03 re-signs the subject digest of the hostile artifact. No cases attempt to forge Ed25519. A06/A07/A08 sign their modified artifact to isolate semantic parsing from signature errors. Every test logs input lengths and classifications without publishing private keys. No test uses arbitrary network input, external authority or real filesystem target paths.

## Halt/anti-retuning

Run the frozen target first, preserve all FAIL and CRASH outputs and workflow exit code. Do not edit VEC-001, revise expected labels or silently skip A01–A03 after inspecting run results. Any repair is a **new post-finding candidate** with a separately named replay, and both runs must remain recorded. A test harness failure before cases execute is an explicit instrument failure and **INCONCLUSIVE** for the unexecuted cases.

## Expected contribution / limitations

Finding a parser recursion crash is a bounded **availability/fail-closed contract** finding, not evidence of signature forgery or unauthorized physical action. Accepting replay/conflicting reports is an explicitly unimplemented cross-evidence / ledger layer, not a newly discovered cryptographic flaw. This is still an author-designed test: no independent external review and no universal totality claim, even if all tests pass later.

## Clarifications before first execution (prospective, same predictions)

- **A06 location:** the duplicated nested key is `predicate.reviewer_role` in the *signed Statement payload*, paired with an otherwise ordinary signed, valid-shaped artifact. This isolates duplicate-key rejection in authenticated metadata. The original table's “artifact” wording was imprecise. Prediction remains REFUSED.
- **A10 scope:** two different signed finite lists under the same study/claim are **competing reports**, but not logically contradictory unless a shared immutable observation-set identity is additionally declared. This profile lacks such an identity and has no batch cross-report verifier. Predict both accepted independently; do NOT claim that finding proves an actual logical contradiction or a violation of VEC-001's contract.
- **Exit semantics:** if an anticipated recursion crash occurs, the harness exits nonzero for an S1 failure even if its prediction matches. No success claim from a green test runner configured to accept failures.
