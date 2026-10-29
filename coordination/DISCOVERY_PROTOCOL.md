# Discovery and breakthrough protocol — v0.1

**Status:** `PROPOSED_FOR_OWNER_REVIEW` · **Scope:** VERITAS ORIGIN, ChatGPT–Claude research exchange · **Date:** 2026-10-09.

## Purpose

Do not lose a potentially important observation just because it emerges during debugging, negative-control testing, model training, mathematical analysis or an AI-to-AI conversation. **Capture first; classify honestly; falsify; independently reproduce; then decide whether implementation or public novelty claims are justified.**

**Breakthrough** is a *retrospective*, evidence-supported description, not a status an AI can award itself. A useful mechanism may already exist in the literature and still deserve implementation. A new-looking benchmark effect may disappear under a stronger baseline or different random seeds. Preserve both.

## Candidate capture — mandatory even before novelty is known

Create `coordination/discoveries/DISC-YYYYMMDD-NNN.md` as a **new append-only candidate note** and add one row to `DISCOVERY_REGISTER.tsv`. No candidate can be deleted for yielding a negative result; supersession is additive. Required fields:

1. **Exact observation:** what was observed (not what it might mean), with source code path, full Git commit SHA, raw run ID, data filename, SHA-256 of **original** evidence bytes and the metric/denominator.
2. **Proposed mechanism and prediction:** causal explanation, proposed mathematical/computational mechanism, what it improves or changes, and **a novel discriminating prediction**, if any.
3. **Scope:** concrete model, data distribution, budget, hardware/runtime, measurement instrumentation and whether the result is exploratory/post-hoc/preregistered.
4. **Alternatives:** simpler known explanations, bugs, task contamination, overfitting, extra tokens/operations, shared-label leakage, baseline weakness or evaluation error.
5. **Prior art:** relevant peer-reviewed papers, existing libraries and patents if pertinent, with working links, dates and a statement of *what appears different*. A search that found no prior art is **NOT proof of novelty**. If search is incomplete, label `PRIOR_ART_UNVERIFIED`.
6. **Falsifiers:** negative controls and matched strong baselines, sample sizes, cost, anti-vacuity controls and explicit conditions that would make the claim fail.
7. **Independence:** which reviewer independently read/reimplemented source, what assumptions were shared and whether outside researchers independently replicated on new data/hardware.
8. **Risk and authority:** privacy/security implications, capability limits, source licenses, who may approve rollout. No secrets or private user data.
9. **State and next owner action:** one of the states below plus a reference to the latest non-rewritten update.

## Evidence-based states (not a single VERIFIED flag)

| State | What it means | What it does **not** mean |
|---|---|---|
| `CANDIDATE_RECORDED` | A specific observation, provenance and hypothesis were archived | True, novel or reproducible |
| `EVIDENCE_INCOMPLETE` | Missing raw data, revision, baseline, or provenance is explicitly documented | Refuted |
| `PRIOR_ART_IN_PROGRESS` | Related established work is being checked | First discovery or patentability |
| `EXPLORATORY_EFFECT_OBSERVED` | Effect was observed within described exploratory conditions | Confirmed effect or general applicability |
| `FALSIFICATION_IN_PROGRESS` | Contradictory tests and stronger controls are underway | Validated |
| `NOT_SUPPORTED` | Prespecified effect/claim failed or falsification found a counterexample | Entire domain disproved |
| `SPECIFICATION_CONSISTENT` | Artifacts agree with a frozen math or verification specification | Source authenticity, methodology or world truth |
| `REIMPLEMENTED_BY_OTHER_AI` | A separately coded implementation reproduces a specified result | Independent external scientific replication |
| `EXTERNALLY_REPLICATED` | Credible outside researcher reproduced specified results under recorded constraints | Universal theory, first-in-world novelty |
| `IMPLEMENTED_EXPERIMENTALLY` | Working code exists on isolated branch with tests and declared limits | Production safety or owner-approved deployment |
| `OWNER_APPROVED_SCOPE` | Human owner has approved a specifically identified next research/deployment action | Universal claims outside that scope |
| `SUPERSEDED` | A later record changes the interpretation while preserving this record | Deletion of the original result |

**Separate axes in every record:** `INTEGRITY`, `NUMERICAL_REPLAY`, `METHODOLOGY`, `ORIGINALITY`, `EXTERNAL_REPLICATION`, and `DEPLOYMENT_AUTHORIZATION`. Each needs its own evidence; neither human approval nor all-green CI implies any other axis passes.

## Escalation gates: novel ≠ works ≠ safe ≠ publishable

**Gate A — preservation.** Append the exact candidate with immutable provenance and negative observations. This may happen on an unmerged coordination branch.

**Gate B — established research review.** Search at least the obvious field precedents, implement simpler baselines and name the closest work. Distinguish a *new combination* from a novel core algorithm and from an application-specific improvement. No unsupported priority/novelty claims.

**Gate C — prospective falsification.** Before collecting new evaluation results, freeze a separate protocol with claim, independent oracle/evaluator identity, new test distributions, effective sample size, matched compute/labels/tokens/wall time, failure/invalid states, analysis plan and stop rule. Negative results remain visible.

**Gate D — independent implementation and replication.** A second implementation may test algorithm mistakes while still sharing a source, fixture or NumPy assumptions. Seek an outside reviewer, distinct data and/or alternate platform for stronger claims. Prevent evaluator contamination and self-reported-clean evidence.

**Gate E — restricted implementation.** If warranted, implement the idea **on a draft experiment branch**, with full tests, threat model, dependencies, pinned sources, rollback path, and `NOT_VALIDATED` label until support improves. Implementation can proceed even if novelty is disproved—provided its engineering value is demonstrated and it is attributed correctly.

**Gate F — public breakthrough claim.** Requires owner authorization, accurate prior-art review, independent replication, documented negative cases and appropriate peer scrutiny. Do not automatically announce, patent, license, merge, deploy, or market the finding. Scientific novelty and inventorship/patent claims may require qualified human and legal review.

If Gate C fails, label `NOT_SUPPORTED` and preserve the experiment. If documentation is inaccessible, label `ACCESS_UNVERIFIED`; avoid fabricated citations or hashes.

## Discovery priority examples: what is *not yet* a breakthrough

- ASP-001's global training regulator was active but **did not beat preregistered baselines**. It is **NOT_SUPPORTED** for that precise advantage claim, not evidence for artificial neurochemistry.
- ITC-001 showed more latent passes improved accuracy over one in a tiny fixture, while adaptive stopping **failed against per-task budget-matched shuffling**; actual masked early execution reduced logical updates but could be slower in wall time. These findings do not establish human thought or theoretical complexity thresholds.
- EPV-001 exhibited a deliberately programmed **poisoned trusted-anchor false positive**. This is a useful adversarial control, not a novel theorem or proof of real agent reliability.
- Sovereign Veritas verification or permission is bounded by its inputs; `CONSISTENT` is never evidence of external truth. A verified hash of a false statement is still false.

These results are valuable precisely because they provide **mechanistic falsifiers** for future hypotheses. A future genuinely surprising effect should be evaluated against these boundaries rather than declared new by analogy.

## Responsibility and attribution

Human owner decides what is public, what may be merged and whether reviewers are credited. Attribute experimental code, AI assistance, external papers and independently observed insights precisely. A model's self-description of its authorship is not proof of originality.

**Default if unsure:** `CANDIDATE_RECORDED / NOVELTY_NOT_ESTABLISHED / NOT_VALIDATED`, with an explicit next falsification test.
