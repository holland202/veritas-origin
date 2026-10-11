# VEC-001 — Evidence Circuit: prospective registration

**Status:** REGISTERED_BEFORE_IMPLEMENTATION / NOT_RUN / NOT_VALIDATED
**Date:** 2026-10-10 America/Chicago
**Author:** GPT-6 with owner permission for creative research. Original DPC-001 v0.1 and frozen v0.2 are NOT changed. This branch is an independent adapter experiment, not a production release or automatic authorization.

## Problem and hypothesis

DPC-001 v0.2 can classify a contract as READY from self-declared attestation and a non-NONE artifact string. The separate Evidence Circuit hypothesis is **narrower**: a bounded *offline* verifier can determine whether provided artifact bytes are digest-bound to an in-toto Statement authenticated by a trusted Ed25519 DSSE signer, bound to study/claim/contract context, and whether a declared maximum agrees with the enumerated finite-set values. Such verification will NOT establish scientific truth of an arbitrary signed claim, statistical generalization, third-party independence, or permission to perform a physical/external action.

**Primary endpoint:** positive fixture P0 yields BINDING_VERIFIED and execution_authorized=false; all preregistered N01–N19 yield REFUSED for a stated reason, without uncaught exceptions; P1 (trusted signed fiction) may still yield BINDING_VERIFIED and is explicitly an expected limitation. Running these checks later is development/self-test only. No hidden test set is implied.

## Input / permitted scope (implementation requirements)

- Offline `verify(envelope_bytes, artifact_bytes, trusted_context, trust_map)`. No network, subprocess, filesystem writes, or tool execution in verification.
- Ed25519 library: maintained `cryptography`; no custom cipher. DSSE pre-authentication encoding must sign **exact raw bytes and payloadType** in protocol order: `DSSEv1 SP len(type) SP type SP len(body) SP body`. DSSE envelope carries base64 `payload`, `payloadType`, a **single** `signatures` entry (`keyid`, `sig`). The untrusted key ID selects *only* a configured trust-map key; it never creates trust.
- The signed bytes contain in-toto Statement v1 with _type, a **single subject** name and sha256 digest of raw artifact bytes, a custom application predicateType, and a strict custom predicate. The application profile is **not** a claim to support all DSSE/in-toto extensions. Their base specifications may ignore extensions, while our application predicate and artifact schema are intentionally closed.
- Trusted context provided separately, not from signed input: expected study_id, claim_id, contract SHA-256, artifact name, role, unit, threshold (strictly positive integer), trusted Unix UTC time; trust map fixed outside envelope. Missing trusted time REFUSE. Key rotation/rollback/signer independence NOT covered.
- Artifact JSON contract with closed keys: schema, study_id, claim_id, units, contrasts (non-empty bounded integer list), declared_max_abs_contrast (nonnegative integer). The verifier recomputes **max(abs(x)) over observed list**; it does NOT infer maximum attainable contrast outside that finite list.
- Predicate has closed keys study_id, claim_id, contract_sha256, reviewer_role, issued_at, expires_at; require signed matching context, trusted signer role and issued_at<=trusted_time<expires_at.
- Strict JSON: reject duplicate object keys, NaN, Infinity and unknown application keys; reject oversized inputs, empty lists, booleans as integers, malformed SHA strings. Strict canonicalization is NOT needed for DSSE; signature covers the exact encoded payload bytes.
- Two independent outputs: `binding_status` BINDING_VERIFIED/REFUSED and `local_arithmetic` finite maximum + only a **descriptive** threshold comparison if verified. `execution_authorized` must be false in **all** circumstances. `READY_FOR_COMPARISON` is NEVER emitted by this adapter.
- All REFUSED states carry stable machine reason codes; no proof of invalid scientific claim is inferred from REFUSED evidence.

## Frozen test cases

| ID | Condition | Expected binding |
|---|---|---|
| P0 | valid locally generated Ed25519 signer, all bindings matching, finite contrasts | BINDING_VERIFIED |
| P1 | trusted key signs internally consistent *but externally untrue* prose/contextual claim | BINDING_VERIFIED (limitation: signatures don't prove truth) |
| N01 | artifact bytes missing | REFUSED |
| N02 | change artifact contrasts to another list with same max, without resigning | REFUSED |
| N03 | tamper signed Statement bytes, preserve old signature | REFUSED |
| N04 | wrong/untrusted signer keyid | REFUSED |
| N05 | empty trust map | REFUSED |
| N06 | change payloadType without resigning | REFUSED |
| N07 | context study_id differs from signed predicate | REFUSED |
| N08 | context claim_id differs | REFUSED |
| N09 | context contract SHA-256 differs | REFUSED |
| N10 | trusted time is expiry boundary | REFUSED |
| N11 | add application evidence top-level status=VALIDATED | REFUSED |
| N12 | duplicate JSON key in evidence | REFUSED |
| N13 | NaN in evidence JSON | REFUSED |
| N14 | declared finite max != recomputed max (re-sign modified artifact) | REFUSED |
| N15 | reviewer role is wrong for configured trusted signer | REFUSED |
| N16 | trusted time absent | REFUSED |
| N17 | empty contrasts list | REFUSED |
| N18 | negative or zero threshold in trusted context | REFUSED |
| N19 | use two signatures in envelope | REFUSED |

## Anti-vacuity / boundaries

- P0 prevents “refuse everything” from passing.
- N02 uses **same maximum, different bytes** to isolate digest binding from arithmetic; N03 isolates signed Statement integrity; N06 isolates payload type binding.
- N14 is fully re-signed, so successful rejection must come from semantic consistency rather than bad cryptography.
- Every result captures version/environment, each case ID, status, refusal reason, actual/expected, and overall process exit. At least one unanticipated result means REFUTED, never silently retune expectations.
- Use volatile test keys only; do not publish private keys as static repository fixtures. No production identities, actual user files, network services or agents used.
- No attack against real systems; no experiment outside local fixtures.

## Layer map (25 independently legible boundaries)

L01 source discovery; L02 retrieval access; L03 revision pinning; L04 license/scope; L05 raw byte acquisition; L06 content-size cap; L07 strict parsing; L08 schema/type integrity; L09 DSSE type binding; L10 signer authentication; L11 trust-anchor selection; L12 signer role; L13 statement predicate selection; L14 subject identity; L15 artifact SHA-256 binding; L16 study binding; L17 claim binding; L18 contract revision binding; L19 time validity; L20 evidence arithmetic; L21 cross-evidence contradiction (FUTURE); L22 scientific generalization gate (FUTURE); L23 authorization gate (FUTURE; never implied by adapter); L24 audit provenance (test harness only initially); L25 rollback/freshness witness ledger (FUTURE). All future layers explicitly NOT IMPLEMENTED.

## External standards / research starting points

DSSE https://github.com/secure-systems-lab/dsse/blob/master/protocol.md ; in-toto https://github.com/in-toto/attestation/blob/main/spec/v1/statement.md ; Sigstore https://docs.sigstore.dev ; TUF https://theupdateframework.io/docs/metadata/ ; OpenAI deliberative alignment https://openai.com/index/deliberative-alignment/ ; Anthropic Petri https://www.anthropic.com/research/petri-open-source-auditing . Reusing ideas does not imply institutional partnership or access to private research.

**Change policy:** any modifications to these predictions after running require dated amendment and preserve the first failing output. Implementation comes after this registration has been committed. No scientific validation claims without independent later review.
