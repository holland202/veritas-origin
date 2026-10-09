# Veritas-Origin 12-Layer Architecture Audit

Status: DESIGN-ONLY / REPOSITORY INSPECTION / 2026-10-09. No experiment was executed. No PR merged. No claim of independently validated capability.

## Scope of evidence
This is a static GitHub source inventory of `main` and the **titles/states** of draft pull requests, not a complete code-level inspection of every PR. Current `main`: README, `src/origin/experiment.py`, `src/origin/exp003.py`, EXP002/EXP003 protocols and tests, tools/verifiers, evidence and reports, and one GitHub workflow `exp003-p0.yml`. Frozen DPC-001 remains on PR #19 at commit `d05501013c7b2d0c602893e44d157620b55f12ff`, with visible/withheld cases on draft PR #20. PR #21 holds the *proposed* prior-art architecture. An open PR's title does not establish that its claim is true.

Maturity labels: **PRESENT_SOURCE** = code/document exists, not an end-to-end validation claim; **DRAFT_PR** = proposed or experimental material not merged; **GAP** = no verified complete implementation; **EXTERNAL** = independently maintained component outside repository.

| Layer | Actual source evidence | Assessment | Evidence needed before integration claim |
|---|---|---|---|
| 1 UI | `README.md`; publication plan proposes a read-only Vercel interface | GAP | Read-only dashboard showing raw failures and pinned manifests, no remote mutation |
| 2 Identity / tenancy | EXP003 proposer relies on caller OS authority; docs warn no sandbox | GAP | Principals, roles, scoped credentials, separation tests, forged-identity refusal |
| 3 Input safety | `src/origin/exp003.py` strict JSON object parsing and bounded external proposal; tests | PRESENT_SOURCE, narrow | Injection/oversized payload/malformed JSON/security-boundary tests; process isolation |
| 4 Data / memory | `evidence/exp002`, `evidence/exp003`, immutable filename approach; reports and verifier tools | PRESENT_SOURCE, partial | Provenance manifests, exact source/runtimes, retrieval trust, access and tamper tests |
| 5 Model / inference | EXP003 external-proposer command (not proof of an LLM); no integrated model runtime in main | PRESENT_SOURCE interface / GAP integration | Pinned local/cloud model adapter, inference/decoding provenance, output grading |
| 6 Runtime / orchestration | EXP003 bounded pilot and policies; `.github/workflows/exp003-p0.yml` | PRESENT_SOURCE, limited | Inter-agent isolation, retries, quotas, cross-run dedup, operational audit |
| 7 Proposal / experimental planning | EXP003 fixed/random/greedy and external proposals; DPC-001 spec PR #19 and test-harness PR #20 | PRESENT_SOURCE for toy lab; DRAFT_PR for DPC | Held-out hypothesis-discrimination result, estimator and split-RNG controls, preregistration |
| 8 Authorization / evidence gate | Sovereign Veritas is separate project; VO PR #10 title describes a boundary | EXTERNAL; no demonstrated VO integration | Real adapter with exact action binding, refusal tests, pinned SV commit/digest |
| 9 Tool gateway / execution | EXP003 can invoke a trusted local external proposer with subprocess; documentation says no sandbox | GAP for protected tools | Fail-closed executor, no-bypass design, idempotency, TOCTOU tests |
| 10 External systems / effects | Evidence files produced locally; no independently established real-world effect verification | GAP | External execution receipts plus separately checked effect identity and uniqueness |
| 11 Observability / independent evaluation | Verifiers `tools/verify_exp002.py`, `tools/verify_exp003_p0.py`; tests/reports; negative findings in draft PRs | PRESENT_SOURCE, limited | Independent evaluator/source custody, complete CI logs, negative outcomes, error bars |
| 12 Infrastructure / supply chain | Python scripts, tests, GitHub workflow; `docs/PUBLICATION_AND_MIRROR_PLAN.md` is planned | PRESENT_SOURCE, limited | Runtime SBOM/lock, reproducible execution, workload isolation, verified mirror/dataset hashes |

## Existing experiments: what the repository actually says
- `src/origin/experiment.py`: deterministic seeded toy bandit policies, immutable evidence filename, SHA-256; self-labels exploratory/not validated. This is **not** a learned scientific model.
- EXP002 preregistration describes UCB1 vs fixed/random Bernoulli baselines, with fixed seeds, outcomes and limitations. Preregistration status is historical source text, not a fresh execution status.
- EXP003-P0 documentation explicitly states its baseline-only pilot is simulated, with no LLM; external proposer is a caller-specified subprocess that is **not sandboxed**. Run only trusted commands. Its verifier checks internal consistency; it shares the specified task model, so it does not establish world truth.
- DPC-001's frozen spec and its withheld cases must not be modified or exposed to an implementation author; code implementation and acceptance remain separately owner-gated.
- Other draft PRs (#7–#18) are research candidates (curriculum, evaluator attacks, independent evaluation, model plasticity, recurrent computation, agent exchange); they are **not yet** part of the canonical `main` architecture.

## Integration contracts worth designing AFTER SV closes
1. `ResearchQuestion`: question ID, hypothesis set, source hashes, preregistered baseline and stop rule.
2. `ExperimentProposal`: question ID, test, budget, action intent, required evidence, predicted discrimination **without revealing oracle truth**.
3. `EvidenceRecord`: runner/machine provenance, input commit, raw output digest, timestamp/ordering, failure state, custody.
4. `ProtectedActionIntent`: authenticated principal, action/resource, immutable argument digest, policy revision, nonce/idempotency value, trusted evidence references. These are *candidate wrapper fields*, not claims about SV package schemas.
5. `AuthorizationDecision`: reference to independently verified SV signed/bound package and applicable trust material; distinguish POLICY_ALLOW from EXECUTED and EFFECT_VERIFIED.
6. `ExecutionReceipt`: executor identity, exact action/args, external receipt/event ID, outcome, failure/retry/reconciliation state. Do not infer exactly-once semantics from a log line.
7. `EvaluationRecord`: pinned evaluator, held-out set custody, per-case result, negative controls, unresolved status, statistical uncertainty, independent party status.

## Critical boundary rules
- Proposal != authorization != execution != externally verified effect.
- Read-only tasks can be autonomous within an active approved scope; a parked project has **no** authorization to launch new experiments.
- Independent AI criticism is useful but correlated AI agreement is not independent replication.
- Digest match verifies bytes, not scientific correctness; signed evidence does not establish truthful claims.
- Preserve SV limitations (DEFAULTED-only ALLOW, declarer/signer ambiguity, first-use anchor, concurrent consumer state race, effect binding not validated).
- The 12 layers are conceptual responsibilities; the system does not need 12 services or 12 repositories.

## Sources checked
- https://github.com/holland202/veritas-origin
- https://github.com/holland202/veritas-origin/pull/19
- https://github.com/holland202/veritas-origin/pull/20
- https://github.com/holland202/veritas-origin/pull/21
- https://github.com/holland202/sovereign-veritas/pull/63
