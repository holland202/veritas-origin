# VEC-003 external review gate — unresolved checklist

**State:** `REVIEW_REQUESTED / INDEPENDENT_REVIEW_NOT_COMPLETED / HOLD_PRODUCTION_MERGE`.
This document states claims to **challenge**, not claims to trust. Author of code, tests, registrations and analyses is GPT-6; a new instance of an AI reviewing the same author's code is at most another AI-assisted review, **not independently established validation**. An independent reviewer must author or select tests outside the visible author-designed set, inspect source/commit history and supply a separate signed or otherwise attributable report.

## Exact test artifacts and provenance

- Original JSON-depth fault: [VEC-002 failed workflow 38109650930](https://github.com/holland202/veritas-origin/actions/runs/38109650930), 3 unhandled RecursionError cases, historical source unchanged in PR #31.
- Post-finding narrow decoder catch repair: PR #32, [R1 run 38109756175](https://github.com/holland202/veritas-origin/actions/runs/38109756175), 15/15 repair checks and 21/21 original checks.
- Prospective VEC-003 registration commit `585996f`, parser preflight commit `b458f22`, exact test runner repair `a569207`, [VEC-003 22/22 workflow 38131778353](https://github.com/holland202/veritas-origin/actions/runs/38131778353); failed harness before test [38131734568](https://github.com/holland202/veritas-origin/actions/runs/38131734568) retained.
- Prospective **after-VEC003** S1 stress registration `7eebdad`, [900/900 hostile/positive S1 workflow 38131916373](https://github.com/holland202/veritas-origin/actions/runs/38131916373), 256 MiB/8 sec RLIMIT child + 15sec parent watchdog.
- The current PR's documentation commits follow the tested code; the last executable source change was `a569207`. Git blob for frozen DPC-001 v0.2 checker `88ece9d3...`, spec `041e4c4e...` checked identical to frozen commit `bc43adf`. No v0.2 modification in this PR.

## Mandatory independent adversarial review questions

1. **Scanner correctness.** Can a syntactically valid UTF-8 JSON input exceeding 64 nested arrays/objects or 4096 punctuation characters outside strings pass `_preflight_json`? Review odd/even backslash runs, escaped double quotes, Unicode escapes, malformed surrogate sequences, misleading non-ASCII whitespace, and cross-parser differentials.
2. **No unjustified acceptance.** Is anything outside the DSSE application profile accepted, such as alternate signed types, duplicate JSON keys, unknown authority-bearing fields, mismatched artifact names or signed reports from unauthorized roles? Verify fail-closed parsing does not replace actual cryptographic checks.
3. **Resource control.** Can a <=65536-byte envelope, <=32768-byte signed payload or <=65536-byte artifact consume excessive CPU/memory even with 64-depth/4096-separator preflight? Check integer/float parsing behavior, base64 allocation, large strings, recursion/stack errors, repeated validations, concurrency and child termination under host-enforced limits.
4. **Trust boundary.** Check hostile caller objects, custom `Mapping.get`, signer identity/keyid collisions, forged-but-valid signed predicate, stale/rolled-back public key sets, compromised signer, absent trusted clock and cross-study replay. VEC-003 does **not** claim these are solved.
5. **Conformance.** Compare DSSE PAE with independently generated vectors or a separate DSSE implementation, including payloadType substitution under a profile that permits two authenticated types. Existing VEC-001 N06 refuses the alternate type **before** signature verification; that test does **not** prove PAE protects type substitution.
6. **Epistemic boundary.** Properly signed yet fabricated experiment values must never silently become scientific truth, `NONDISCRIMINATING_ENDPOINT`, `READY_FOR_COMPARISON`, or an external action permit. An artifact digest is not a claim-support proof.
7. **Platform coverage.** Re-run with exact source and dependency hashes on an independent substrate, including (if available) Android/Termux ARM64; do not assume Ubuntu CI transfers to an edge device.
8. **Audit evidence.** Capture commit SHA, file SHA-256 (not just Git blob SHA-1), full commands, environment, stdout/stderr and exit codes, negative cases, and conflicts. Review original failures and incremental repairs without averaging away the failures.

## Merge gates

**Production/main merge: HOLD.** External attack-case authoring and review not complete; no verified real enforcement boundary, key-root history, runtime timeout guarantees across deployments, or scientific validation. **Experimental PR #33:** remain draft until review answers are logged; maintain the branch dependency chain #30→#31→#32→#33 without flattening failures. Reviewers may raise new findings and create separately registered amendments; do not edit prior executed results.
