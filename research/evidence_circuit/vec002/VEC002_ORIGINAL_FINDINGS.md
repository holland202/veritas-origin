# VEC-002 initial adversarial findings — original target, no repair applied

**Status:** `OBSERVED / S1_FAIL / NEGATIVE_PRESERVED / NOT_INDEPENDENTLY_VALIDATED`
**Preregistration:** `VEC002_PREREG.md` committed at `7c86df9f993cc0828c3b9dc3985baf6f5ee72c37` before harness and execution; its before-run clarification was committed `d27c9f6bea4e990de9dc3ed4b0b65cebd746594a`.
**Unchanged VEC-001 target:** Git blob SHA `b328a241c498941af8807954050a0ca6af959010`; VEC002 PR #31 changes no VEC-001 implementation.
**Environment:** GitHub Actions Ubuntu 24.04, CPython 3.11.17 x86_64, pinned cryptography==46.0.4; ephemeral keys only.

## Original execution

- VEC-002 registered adversarial workflow run [38109650930](https://github.com/holland202/veritas-origin/actions/runs/38109650930), job `114382382506`, **FAIL exit 1**.
- VEC-001 original controls [38109650919](https://github.com/holland202/veritas-origin/actions/runs/38109650919), job `114382381852`, **SUCCESS**, `21/21` original registered cases.
- VEC-002 `PREDICTIONS 15 / 15`; **typed-refusal invariant failure** `S1_TYPED_REFUSAL_FAIL_CASES A01,A02,A03`; `PREDICTION_MISMATCH_CASES NONE`; `VERDICT FAIL`.
- A01: deeply nested unsigned JSON envelope (3,001 bytes) → `CRASH:RecursionError`.
- A02: correctly signed deeply nested DSSE payload inside envelope (4,199 bytes) → `CRASH:RecursionError`.
- A03: correctly signed subject digest for deeply nested artifact JSON (envelope 811 bytes, artifact 3,001 bytes) → `CRASH:RecursionError`.
- C00 authentic fixture → BINDING_VERIFIED; A04/A05 untrusted map/key → REFUSED; A06 signed duplicate nested key → REFUSED; A07 NaN → REFUSED; A08 huge exponent → REFUSED; A11 expired time → REFUSED; A12 two signatures → REFUSED.
- A09a/A09b exact replay → BINDING_VERIFIED twice; no replay protection built. A10a/A10b differing finite-list reports → BINDING_VERIFIED individually; no cross-report comparison; cannot infer logical contradiction without same immutable observation identity.

## Failure mechanism

`vec001._json` converts `ValueError` and `UnicodeError` to `Rejection`, but Python's JSON parser can raise `RecursionError` on a well-bounded (~3 KB) deeply nested JSON array. `verify` catches `Rejection` plus TypeError/KeyError/ValueError/OverflowError, but does **not** catch `RecursionError`. Thus an in-bounds hostile input escapes with an exception instead of returning a typed `REFUSED` result.

The principal claim is *bounded input totality*; this result refutes it for these three cases. It does **not** demonstrate a broken Ed25519 signature check, false scientific proof, unauthorized action, remote access or production exploit. Keep this negative result even if a subsequent candidate fixes the three examples.

## Proposed follow-up, not part of original registered run

In an explicitly separate repair candidate, convert parser `RecursionError` into a stable typed REFUSED reason without changing cryptographic checks; then run original VEC-001 controls plus a **new prospectively registered repair matrix** on the same A01–A03 and other cases. The original VEC-002 predictions must remain untouched: a good fix will intentionally make their predicted CRASH classifications cease to match. Do not treat this as rewriting the original experiment.

**Next independent work:** fuzz around recursion limits, other exception types, huge integer literals/CPU budget, trust-map tampering, and external protocol vectors, on separate preregistrations.
