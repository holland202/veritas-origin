# The Evidence Circuit — a layered research architecture

**State:** VEC-001 exploratory prototype on separate branch; **NOT validated, not deployed, not an AGI or a trustworthy execution gate**. VEC-001 freezes only the predictions stated in `VEC001_PREREG.md`. This design note is a post-registration architectural elaboration, not a silent change to those predictions.

## Five zones and 25 meaningful interfaces

A large number of layers is useful **only when each has a distinct invariant, adversarial bypass case, and explicit failure response**. These zones are not a substitute for end-to-end coverage or independent review.

| Zone | Layer / concern | Required invariant | Prototype |
|---|---|---|---|
| Acquisition | L01 Source discovery | source origin displayed, not mistaken for truth | future |
| Acquisition | L02 Retrieval access | blocked or private pages marked unverified | future |
| Acquisition | L03 Revision pinning | revision/tag recorded before downstream use | future |
| Acquisition | L04 License/scope | usage rights and dataset boundaries recorded | future |
| Acquisition | L05 Raw byte acquisition | processing starts from exact bytes, not excerpts | partially (caller supplied bytes) |
| Parsing | L06 Size caps | no oversized input accepted | implemented |
| Parsing | L07 Strict decoding | duplicate keys and nonfinite literals rejected | implemented |
| Parsing | L08 Application schemas | unknown authority-bearing fields rejected | implemented for local profile |
| Authentication | L09 DSSE payload type | type and bytes pre-authenticated (PAE) | implemented via signed raw bytes |
| Authentication | L10 Ed25519 signature | valid under trusted public key | implemented |
| Authentication | L11 Trust anchoring | key comes from out-of-band trust map | implemented |
| Authentication | L12 Reviewer role | signer role matches trusted role | implemented |
| Attestation | L13 Predicate type | only registered local predicate | implemented |
| Attestation | L14 Subject identity | exact named artifact | implemented |
| Attestation | L15 Digest binding | raw artifact SHA-256 matches statement | implemented |
| Attestation | L16 Study identity | matches trusted context | implemented |
| Attestation | L17 Claim identity | matches trusted context | implemented |
| Attestation | L18 Contract revision | pinned SHA-256 matches trusted context | implemented |
| Attestation | L19 Time limits | attestation valid at trusted injected timestamp | implemented; no rollback witness |
| Semantics | L20 Local arithmetic | recompute maximum of finite **observed** list only | implemented |
| Semantics | L21 Cross-evidence contradiction | different evidence sources cannot silently override conflict | future |
| Semantics | L22 Scientific generalization | observed list is not attainable upper bound or target-population proof | future; always disclaimed |
| Authority | L23 Authorization | evidence validity cannot authorize a real-world action | refusal to authorize implemented; actual gate future |
| History | L24 Audit provenance | record exact test paths, exit statuses and negative outcomes | harness prints results; trusted log future |
| History | L25 Anti-rollback witness | truncation, swapped trusted roots or stale snapshot detected | future |

### Proposed control flow

```text
UNTRUSTED RESEARCH INPUTS
   -> SOURCE REGISTER -> EXACT BYTES -> STRICT SCHEMA
   -> DSSE SIGNATURE <---- TRUSTED KEYSET (out-of-band)
   -> in-toto SUBJECT HASH ----> PROVIDED ARTIFACT BYTES
   -> study+claim+contract+role+time binding <---- TRUSTED CONTEXT (out-of-band)
   -> FINITE-SET ARITHMETIC
   -> EVIDENCE STATUS {BINDING_VERIFIED | REFUSED}
   -> SCIENTIFIC ADMISSIBILITY (future independent reviewer)
   -> ACTION AUTHORIZATION (distinct Sovereign Veritas gate; future)
   -> EXECUTION/WITNESS LOG (future)
```

### Why authenticated evidence isn't true evidence

A verifier can check an Ed25519 signature on a signed report asserting that 8 experiments succeeded; it cannot infer whether those experiments happened. VEC-001's P1 deliberately demonstrates this boundary using manufactured finite-set values. A purported upper bound from the largest **observed** contrast is not an analytic ceiling on all attainable contrasts. Thus the adapter never labels `NONDISCRIMINATING_ENDPOINT` or `READY_FOR_COMPARISON`.

Similarly, a valid signature by an authorized signer does not show signer independence or absence of collusion. Rotation, revocation, denial-of-service, time trust, root compromise, rollback, and cross-platform deployment require additional tests. The verifier can reject a missing trusted timestamp but cannot conjure a trustworthy clock.

### Standards and primary research used

- DSSE protocol and PAE: https://github.com/secure-systems-lab/dsse/blob/master/protocol.md ; envelope: https://github.com/secure-systems-lab/dsse/blob/master/envelope.md
- in-toto Statement/Envelope v1: https://github.com/in-toto/attestation/blob/main/spec/v1/statement.md ; https://github.com/in-toto/attestation/blob/main/spec/v1/envelope.md
- Sigstore: https://docs.sigstore.dev/ ; TUF: https://theupdateframework.io/docs/metadata/
- OpenAI [Deliberative alignment](https://openai.com/index/deliberative-alignment/), [Weak-to-strong generalization](https://openai.com/index/weak-to-strong-generalization/), and published Model Spec: specification-conditioned reasoning and oversight research **do not** confer enforcement.
- Anthropic [Petri](https://www.anthropic.com/research/petri-open-source-auditing) and [Automated researchers can reliably mitigate alignment failures](https://www.anthropic.com/research/automated-researchers-mitigate-alignment-failures): useful candidate approaches to broad automated adversarial exploration. Their published results are not direct evidence for VEC-001's correctness.

No claim of access to unpublished OpenAI or Anthropic data; citations identify public documents. A public paper, repository README or agent evaluation report still requires a reproducible source manifest before becoming an experiment's external evidence.

## Evaluation and promotion criteria

The local experimental matrix P0/P1 and N01–N19 is **author-designed and visible**; passing it is not an independent security evaluation. Reproducibility requires the source hash, cryptography version, exact Python/runtime, outputs, exit code, and external reviewer. Any new test added after inspecting results must be marked exploratory or registered as a prospective amendment before execution.

**Promotion gate:** Do not merge this experimental verifier into production or say it enforces security without independent implementation review, external forgery tests, resource-exhaustion tests, bad-trust-clock/root experiments, and a separately verified action boundary. DPC-001 v0.2 remains untouched throughout.
