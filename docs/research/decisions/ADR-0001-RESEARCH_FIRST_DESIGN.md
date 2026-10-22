# ADR-0001 — Research-led design and prior-art control

- **Status:** PROPOSED
- **Date:** 2026-10-08
- **Scope:** VERITAS ORIGIN research program and proposed links to the owner's other projects
- **Decision authority:** repository owner; no automated code/release permission is granted by this ADR
- **Evidence:** pinned source registry `research/prior_art_register.json`; repository baseline `2131d9166deea94811155a746e57fb597491f53a`

## Context

The existing research has valid narrow successes—EXP002/P0 consistency replay and tests—but it does not establish isolated model discovery. Established projects already implement key mechanisms: authorizers, evaluation sandboxes, attested build provenance, transparency logs, model probes and policy engines. Claiming invention of these elements or copying source without proper rights would distort the research.

## Decision

**Adopt research-first development on every substantive module:**

1. A question and its falsifier;
2. Prior-art and own-project review with immutable source references;
3. License and provenance review that distinguishes reference-only material from copied source;
4. Explicit alternative options and a *non-novel by default* assumption;
5. Minimal versioned implementation, strong deterministic control, attack attempts and anti-vacuity tests;
6. Preserved original evidence and independent replay;
7. Human sign-off before merging, deploying or changing authority policy.

This is the default workflow to *propose* for the whole VERITAS ORIGIN build. It is not sufficient for safety certification or legal clearance.

## Alternatives considered

| Option | Benefit | Failure mode / reason not selected |
|---|---|---|
| Implement every idea from scratch | Control of source | Reinvents known approaches, increases audit burden, may duplicate user's own repos |
| Copy from open-source repositories | Faster development | Easy to omit license/notice, inherit vulnerabilities, blur provenance and claimed novelty |
| Integrate a third-party framework as overall authority | Mature tooling | Could conflate tool/execution controls with scientific truth and policy authorizations |
| **Compose small tested interfaces, cite prior art and preserve negatives** | Clear ownership of contracts, falsification-focused, lowest immediate resource cost | Integration and sandbox security still need separate proof |

## Near-term design priorities

1. **Do not attach external model as trusted evaluator.** Build a minimal, separately privileged/oracle-isolated execution adapter and run attempted secret access, egress and descendant-process negative tests. Failure must produce DEFER/REFUSE, not continued execution.
2. **Require external enforcement of total budget.** A timeout, max-token instruction, or CLI flag is insufficient for an untrusted subprocess.
3. **Version research/evidence contracts before migrating components.** Each cross-repo dependency must declare license state, pinned revision, schema, negative tests and rollback story.
4. **Use existing statistical and policy algorithms as explicit baselines.** Novelty, if any, should rest on testable combinations and failure-handling mechanisms, not the reuse of known primitives.
5. **Keep deployment/publishing read only by default** until provenance/authentication and manifest freshness checks are independently exercised.

## Acceptance for this ADR

- Readable architecture and source register show actual overlap and unknowns, not polished novelty claims.
- A CI gate rejects absent source revisions, ambiguous license assertions and attempted promotion from study-only to code copy without explicit review.
- Tests verify that the **gate itself fails** when key requirements are violated.
- No existing evidence or source code is overwritten.
- At least one real security limit (EXP003-P1 shared process authority) remains openly `UNMET`.

## Known limitations

- Source scan is partial; no patent search or legal clearance conducted.
- A human could falsify or omit register declarations; automated structure checks cannot detect every omitted source.
- User's repos are separate products with unproven conformance; do not claim integration.
- All current P1 results are engineering/synthetic; no real-model scientific claim.

## Revisit when

A new dependency is introduced, third-party material would be imported, a model can reach evaluator state, external deployment or finance authority changes, a confirmatory experiment is proposed, or an independent reviewer finds a counterexample.
