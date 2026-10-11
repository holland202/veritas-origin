# VEC-001 — primary-source protocol audit (static only)

**Status:** `STATIC_STANDARDS_CROSSCHECK / NOT_CONFORMANCE_TESTED / NOT_INDEPENDENT`.
Reviewed after the first recorded CI success. This file adds no new test case and changes no VEC-001 registered prediction or implementation.

## Primary documents actually read

| Source | GitHub blob SHA as retrieved | Relevance |
|---|---|---|
| [DSSE protocol.md](https://github.com/secure-systems-lab/dsse/blob/master/protocol.md) | `75dfb56e2437ca698003d6dde6f53b422e614fd1` | signature over byte-level PAE, untrusted keyid hint |
| [DSSE envelope.md](https://github.com/secure-systems-lab/dsse/blob/master/envelope.md) | `2af1a5b0d64624d8c9ecb7c59dc7aab7d802fc66` | JSON envelope fields, multiple signatures and extension handling |
| [in-toto Statement v1](https://github.com/in-toto/attestation/blob/main/spec/v1/statement.md) | `630f773cb530fe5989fe2dbc30e7f73239cd943a` | statement type and subject digest binding |
| [in-toto parsing rules](https://github.com/in-toto/attestation/blob/main/spec/v1/README.md) | `6007b434f79637ad6aa39dd116ca11ba93f0d8ce` | extensible parsing: unknown fields normally ignored |

These are Git **blob SHA-1** identifiers of fetched text (not SHA-256 content manifests), and their displayed default-branch links can move. Future complete replication should pin commit SHA, UTC retrieval, full source bytes and SHA-256 in `SOURCE_MANIFEST.tsv`.

## Static correspondence

1. The VEC-001 `pae` function uses DSSE v1's documented `DSSEv1 SP byte-length(type) SP type SP byte-length(body) SP body`. The payload type string is encoded UTF-8; signature verification uses the **exact signed payload bytes**, without JSON canonicalization. **STATICALLY CONSISTENT**; not independently conformance-tested with official protocol vectors.
2. DSSE describes `keyid` as an **unauthenticated hint**. VEC-001 uses it only to select an out-of-band configured public key and then verifies the signature. **STATICALLY CONSISTENT** with this aspect.
3. The in-toto Statement specifies a subject digest, `_type`, `predicateType`, and typed predicate; VEC-001 checks each within a constrained local profile. **STATICALLY CONSISTENT** with these named fields.
4. **Intentional stricter profile, not standards-wide compatibility:** DSSE permits multiple signatures and optional keyid; VEC-001 requires exactly one signature and a keyid. DSSE/in-toto consumers normally ignore unrecognized extension fields; VEC-001 refuses unknown application envelope/statement/predicate/evidence fields. These are *local verification-policy choices*, not claims that standards require such rejection.
5. In-toto permits richer subjects and predicates; VEC-001 supports one named SHA-256 subject and one custom predicate only. It has not implemented Sigstore trust bundles, certificate identity, transparency verification, revocation or TUF metadata.

## Negative / limitations kept visible

- Registered N06 returns `PAYLOAD_TYPE_INVALID` **before signature checking**. This passes its expected REFUSED outcome but does not exercise cryptographic detection of a payload-type substitution inside a DSSE implementation that accepts multiple types. Separate conformant vector tests are needed.
- P1's 'externally untrue' framing is conceptual. The visible case contains **manufactured values with no independent empirical ground truth**; its signature and finite arithmetic match, but no experiment establishes an external truth claim. This illustrates a logical limit, not a measured false-positive rate.
- Inspection by the same model that wrote code can miss correlated assumptions. The observed CI 21/21 remains a **visible self-test**, not a credential, certification, third-party audit or platform integration.

**Next experiment candidates (NOT preregistered or executed):** a cross-implementation DSSE known-answer vector, property tests under malformed nested types, independent review of reason-code precedence, bounded-size fuzzing, and a real immutable source-manifest demonstration. None may rewrite original VEC-001 predictions.
