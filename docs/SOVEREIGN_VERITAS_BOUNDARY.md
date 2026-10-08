# Sovereign Veritas → VERITAS ORIGIN research authorization boundary

**Status: READ-ONLY CONTRACT ADAPTER / NO AUTOMATIC APPROVAL.**

Source: [Sovereign Veritas](https://github.com/holland202/sovereign-veritas) main commit **`709da9eb435cbfe06a1ca00427843b12c673ceb0`**, root **MIT** license, `CONTRACT.md` `sv.gate/0`. The Gate decision implementation, its separately re-computing package verifier, and its 4690-vector conformance contract are not modified or copied. A successful SV Gate call does not establish methodological validity or physical-world truth.

## Why use it here

SV's Gate distinguishes `ALLOW`, `DEFER`, and `REFUSE` based on the caller's **recorded** evidence, capability, policy and runtime. VERITAS ORIGIN needs this separation specifically between *research evaluation* and *authorization to publish/deploy*. Both components must be used honestly:

- The independently replayed EXP003-P0 pilot supports only `INTERNAL_CONSISTENCY`. It supplies no authorization to publish a stronger scientific claim.
- New candidate claims must be bound to exact source revision, candidate digest, protocol digest, evaluator identity and evidence digest *before any human decision*.
- A human approval must be independently authenticated and scoped to the precise action; merely writing `reviewer: Chad` or `authorized:true` into JSON is **NOT authentication**.
- An unsigned SV package may be rewritten consistently and still verify; a signature without freshness/provenance is likewise insufficient.
- SV has documented concurrent-execution and external-effect receipt limits. In RA-001 there is **no external effect executor**, so no atomic-execution safety claim.

## Read-only adapter structure

`tools/sv_research_bridge.py` generates an explicitly **unauthorized** `sv.gate/0`-shaped input for a candidate claim and `publish_research_claim` action, with metadata booleans that are initially **False** for methodology approval and human authority. The bridge has no path to change these to true in production. It never writes an approval, promotes a claim, calls an external publication API, or executes an untrusted proposer.

| Gate input | Source | Trust |
|---|---|---|
| `record.input_digest` | SHA-256 of exact bounded candidate claim JSON | Content reference only |
| `record.verification.status` | `PASS` for independently verified **internal** archive consistency | Not scientific truth |
| `record.metadata.archive_integrity` | RA-001 read-only archive verifier | Local self-tested assertion |
| `record.metadata.methodology_reviewed` | `false` pending external review | Never set from replay alone |
| `record.metadata.human_approval_verified` | `false` until signed/external approval validator exists | Never set from a caller-controlled field |
| `capability.authorized` | `false` in production adapter | No permission token to publish |
| `policy.allow_only` | `[publish_research_claim]` | Declared scope, not authentication |
| `runtime` | `unknown` until measured or attested outside the model | Defaulted “healthy” runtime is prohibited |

**Expected live bridge result: REFUSE** from missing authorization, even if original archive integrity is true. In isolated synthetic integration tests, explicitly fabricated review/authorization/runtime values may demonstrate that the actual SV Gate has a reachable positive path. Those fixtures must be labeled `SYNTHETIC_ONLY` and never mistaken for an actual publication approval.

## Closing the authorization gap later

A future independent approval service can accept a signed structured decision covering `candidate_sha256, source_commit, protocol_sha256, evaluator_sha256, evidence_manifest_sha256, requested_action, scope, approving_identity, approval_timestamp`, verify signature and freshness, then mint a short-lived **intent-specific** capability. SV must recompute its recorded decision in a package. The real publication executor also needs durable reservation and effect receipts to prevent a second action from racing a ledger write.

None of that is implemented in RA-001. **This branch contains no path to autonomous deployment or self-promotion.**
