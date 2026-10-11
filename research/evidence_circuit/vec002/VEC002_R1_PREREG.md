# VEC-002-R1: prospective post-finding recursion repair

**State:** PROSPECTIVE_REPAIR_PLAN / BEFORE_PATCH / BEFORE_REPLAY / NOT_VALIDATED
**Date:** 2026-10-10 (US Central)
**Target of repair:** experimental `research/evidence_circuit/vec001.py` only. This is a distinct post-finding study from VEC-002's original registration (`7c86df9`), failed run `38109650930`, and append-only finding `422c598`. All original VEC-002 predictions, outcomes, and unmodified target SHA remain preserved on PR #31.

## Hypothesis R1

In the current VEC-001 adapter, convert a JSON parsing `RecursionError` into the ordinary `Rejection("MALFORMED_JSON")` typed result. Do not change DSSE preauthentication encoding, Ed25519 verifier, trust semantics, evidence schema, signatures, role checking, finite-set arithmetic, or action authorization.

**Repair scope:** inside `_json()`, add `RecursionError` to the handled decoder exceptions. A broad `except BaseException` is forbidden. Do not claim arbitrary Python input totality or resource-exhaustion safety from this repair.

## Predeclared acceptance

- On the three original *unchanged* hostile bytes cases A01–A03, expected **`REFUSED/MALFORMED_JSON`**, not CRASH. `execution_authorized=false`.
- Original VEC-002 C00 and A04–A12 continue to satisfy the same narrow protocol behavior, including replay and individually valid competing reports being accepted. Their known gaps are not to be 'fixed' by a silent change of scope.
- The original VEC-001 matrix P0/P1, N01–N19 continues 21/21 with exact same result classifications and refusal codes.
- Controls: require C00 valid BINDING_VERIFIED and P0/P1 in VEC-001, thus can't pass by refusing all; retain separate expected codes for A04 etc. Both workflows must exit 0 for the candidate acceptance status.
- All three recursion cases must remain <= existing size cap so rejection is about parsing depth, not simply input size.
- Every result retains `execution_authorized=false`; return of any unhandled exception is FAIL.
- Explicitly identify this as a **post-finding correction**, not an independent blind replication of the original negative finding.

## Gates

A candidate patch that passes is only `LOCAL_REPAIR_SELFTEST_PASS` (visible author-derived fixtures); it does not establish general absence of parser exceptions. An original-test FAIL and a repair-test PASS are separate facts; neither erases the other. Promote to production only after outside review, additional fuzz and runtime resource tests, offline key-store and trust-history review, and independently verified action boundary. Frozen DPC-001 v0.2 remains unchanged.
