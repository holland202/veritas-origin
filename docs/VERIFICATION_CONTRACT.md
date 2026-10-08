# VERITAS ORIGIN verification contract (RA-001)

**What a verifier can prove is bounded by the precise contract it executed.** A passing hash does not establish that the underlying observation is true, an experiment is valid, or publication was authorized.

| Layer | Input | Output | Meaning | Cannot establish |
|---|---|---|---|---|
| V0 — artifact integrity | Original bytes and externally recorded digests | `BYTE_MATCH / BYTE_MISMATCH` | Exact bytes match pinned Git SHA-1 blob and, where recorded, SHA-256 | Who authored it, time of creation, truth |
| V1 — internal consistency | Full EXP003-P0 JSON + independent verifier | `CONSISTENT / INCONSISTENT` | Recorded decisions obey the published algorithm | Oracle independence, unbiased tasks, real-world performance |
| V2 — historical replay | Original source revision, inputs and conditions | `REPLAY_MATCH / REPLAY_MISMATCH / NOT_EXECUTED` | Declared algorithm reproduces expected archived outcomes | Fresh execution on another environment or world truth |
| V3 — fresh replication | Separate environment/new execution | `REPLICATED / FAILED / NOT_EXECUTED` | Repeated execution matches prespecified tolerances | Scientific validity of the original hypothesis |
| V4 — methodological review | Frozen protocol, baseline, leakage checks, sampling, integrity, complete run inventory | `SCOPE_ACCEPTABLE / INVALID / REVIEW_REQUIRED` | Whether evidence is admissible for a *specific claim* under explicit assumptions | Absolute truth outside the task |
| V5 — claim-promotion / action authorization | Candidate hash, protocol, evaluator identity, human approval, policy, runtime | `ALLOW / DEFER / REFUSE` under an actual externally controlled capability | A particular, bounded action was authorized under supplied inputs | That published claim is true, that effects happened, atomic execution |

## EXP003-P0 current state

- V0: original archived file is pinned by SHA-256 and Git blob SHA1.
- V1: `tools/verify_exp003_p0.py` reconstructs all 36 task-policy evaluations and 86 binary probes; the gate agrees with the *specified mathematics*.
- V2: the original evidence and existing verifier are reproducible by a fresh clone; this is distinct from executing fresh model runs.
- V3: **NOT EXECUTED for independent physical validation**. Separate seed/run experimentation needs its own preregistration.
- V4: the original primary completion endpoint is subject to a 100% ceiling; 2.00 probes/task for greedy is *post-hoc descriptive*, not a preregistered improvement result.
- V5: **NOT AUTHORIZED**. No model, no system test, and no result automatically grants publication/deployment authority.

## Required failure injection and detector placement

| Injected fault | Expected failure layer | Executable control |
|---|---|---|
| Original evidence byte edited (even if a mutable JSON manifest is resealed) | V0 `BYTE_MISMATCH` | `test_archive_evidence_byte_mutation` |
| Missing original pilot file | V0 `BYTE_MISMATCH` | `test_missing_historical_artifact` |
| Historical protocol or runner changed | V0 `BYTE_MISMATCH` | `test_frozen_protocol_or_code_change` |
| Modified report arithmetic | V0, or V1 for modified JSON summary | `test_report_change`, `test_falsified_ledger_counts` |
| Missing policy result / seed | V1 internal consistency | `test_missing_policy_record` |
| Marking post-hoc efficiency as confirmatory | V4 protocol violation | `test_false_confirmatory_promotion` |
| Proposer sees hidden answer / obtains evaluator filesystem access | V4 protocol violation; C1 **NOT IMPLEMENTED** | **OPEN: requires OS/process/network isolation** |
| Changed evaluated candidate digest | V5 authorization mismatch | **OPEN: no authenticated approver/receipt** |
| Self-authorized publication based only on `CONSISTENT` | V5 `REFUSE` | SV bridge integration tests |

A report can be simultaneously `BYTE_MATCH`, `CONSISTENT`, and `SCOPE_INVALID`. Those are not contradictory; they describe different predicates. **Do not collapse their conjunction into a bare `VERIFIED` badge.**

### Fresh-run requirements before making a new hypothesis claim

Freeze hypotheses, baseline, candidate selection, task-generation and difficulty, trial count, stop rules, random seeds handling, token/compute costs, missing-output handling, outcomes, preregistered uncertainty analysis and security boundary. Publish deviations separately as amendments, and never delete negative evidence.

This contract borrows the principle from [Sovereign Veritas's phase-one epistemic design](https://github.com/holland202/sovereign-veritas/blob/main/docs/PHASE_1_EPISTEMIC_IMPLEMENTATION.md): **L1 computational verification, L2 evidentiary support, and L3 domain appropriateness are separate assessments**. Its epistemic data currently do not automatically change the Gate's decision, and VERITAS ORIGIN must not claim that they do.
