# DPC-001 — Discrimination and Information-Value Precheck (DRAFT v0.1)

**Project:** VERITAS ORIGIN  
**Authority:** Chad Holland's recorded `APPROVED_WITH_SCOPE` decision, [coordination PR #16, owner-decision comment](https://github.com/holland202/veritas-origin/pull/16#issuecomment-6083942081).  
**Authorship:** ChatGPT (self-declared), 2026-10-09; source review and methodological design only.  
**Status:** `DRAFT_FOR_OWNER_REVIEW / NOT_FROZEN / NOT_IMPLEMENTED / NOT_VALIDATED`.  
**Scope:** Specification and subsequent independent test design only. NO new model run, scientific experiment, checker implementation, merge to main, deployment, or external action is authorized by this document.  
**Prior discussion:** ChatGPT [EX-003, PR #18](https://github.com/holland202/veritas-origin/pull/18) and Claude [EX-004, PR #17](https://github.com/holland202/veritas-origin/pull/17).  
**Novelty:** `PRIOR_ART_EXISTS` — prospective power/feasibility checks, strong-baseline selection, simulation-based design, pre-analysis plans and analytic control tests are established practice. This is a local enforcement proposal, not a discovery claim.

## 1. Objective, narrow claim and explicit exclusions

**Objective:** Before a *future* study executes, identify whether its registered endpoint could make a **meaningful, interpretable** comparison within the declared observation, budget and epistemic constraints; distinguish known demonstrations, structural tests and genuinely uncertain empirical comparisons. Preserve honest uncertainty rather than manufacture a green pass.

**DPC-001 claim (to test later):** Given a frozen study contract and admissible pre-outcome information, a rule-based checker can assign one of the six dispositions below while (a) preventing trivial always-block behavior through positive controls, (b) preventing always-ready behavior through negative controls, and (c) avoiding post-hoc changes to earlier registered results. This is a claim about correctly enforcing the stated review contract on specified fixtures, **not** general validity of future scientific findings.

**Not in scope:** guaranteeing statistical power, discovering novelty, proving model intelligence, determining world truth, authenticating files by their hashes alone, authorizing experiments, or declaring past exploratory research invalid. A precheck is an aid to *human prospective design*, not a result oracle.

## 2. Unambiguous output contract

Produce exactly **one primary disposition**, plus orthogonal annotations and reasons. The labels are classifications of a *study design against a declared claim*, **not** experiment result labels.

| Primary disposition | Meaning | May run new science solely because of this? |
|---|---|---|
| `CONTRACT_INVALID` | Required definitions missing/contradictory, irreversible leakage, unverifiable claim of authority, or the proposed interpretation exceeds what the endpoint measures | No |
| `STRUCTURAL_TEST` | A bounded deterministic fixture tests a named invariant/threat shape, with a working positive and negative control; **not** an observed population rate | No |
| `NONDISCRIMINATING_ENDPOINT` | Pre-outcome mathematical or admissible independent-calibration evidence establishes that the required threshold or variation cannot be reached under the claimed allowed inputs/resources | No |
| `DEMONSTRATION` | Technically discriminating but primarily illustrates a known result or wins only against inadequate comparators for the *stated* contribution; not a useful test of the promoted novel/comparative claim | No |
| `INSUFFICIENT_INFORMATION` | Design may be informative, but unknown attainable headroom, variance, sample size, leakage separation, baseline feasibility, or forecasts prevents a defensible readiness finding | No |
| `READY_FOR_COMPARISON` | Prospective contract names strong relevant baselines and estimates an attainable, meaningful, uncertain contrast within data/resources/precision boundaries | No; owner authorization remains necessary |

**Precedence:** (1) `CONTRACT_INVALID` for defective contracts/misleading estimands; (2) `STRUCTURAL_TEST` for adequately scoped structural contracts; (3) `NONDISCRIMINATING_ENDPOINT` for *proven* lack of contrast; (4) `DEMONSTRATION` for known/trivial comparison as framed; (5) `INSUFFICIENT_INFORMATION` if any mandatory readiness evidence is missing; (6) `READY_FOR_COMPARISON` only when all necessary conditions are affirmatively supported. No fallback from missing evidence to READY.

**Orthogonal fields:** `claim_kind` = `STRUCTURAL | DESCRIPTIVE_RATE | COMPARATIVE_EFFECT`; `review_phase` = `PROSPECTIVE | RETROSPECTIVE_DIAGNOSTIC`; `reason_codes[]`; `limitations[]`; `contested[]`; `strongest_baseline_status` = `DOCUMENTED | MISSING | EXCLUSION_JUSTIFIED | UNRESOLVED`; `forecast_status` = `ANALYTICALLY_PREDICTABLE | PREDECLARED_FORECAST | UNCERTAIN | UNAVAILABLE`; `replay_status` = `NOT_RUN | SOURCE_INSPECTED | REPLAYED | ACCESS_UNVERIFIED`. Existing experiment hypothesis outcomes must remain separate.

**Rule:** `READY_FOR_COMPARISON` never means `VERIFIED`, `AUTHORIZED`, `SUPPORTED`, `NOVEL` or `COMPLETE`.

## 3. Required study-contract fields (before writing the checker)

This document defines a future machine-readable *schema*; the structure below is illustrative, not running code. Each key listed is required; use explicit `UNKNOWN` with justification when unavailable, which generally forces `INSUFFICIENT_INFORMATION` or `CONTRACT_INVALID`, not silent defaulting.

```json
{
  "schema": "dpc-study-v0.1",
  "study_id": "EXAMPLE-NOT-A-REAL-STUDY",
  "review_phase": "PROSPECTIVE",
  "source": {
    "repository": "owner/repo",
    "revision_sha": "PIN_FULL_GIT_SHA",
    "protocol_path": "path/to/frozen/protocol.md",
    "protocol_sha256": "PIN_64_HEX_SHA256",
    "fixture_or_generator_revision": "PIN_OR_UNKNOWN",
    "evidence_provenance": "SOURCE_LIST_OR_UNKNOWN"
  },
  "claim": {
    "claim_kind": "COMPARATIVE_EFFECT",
    "hypothesis": "Precise falsifiable claim",
    "intended_contribution": "novel advantage / replication / correctness / demonstration",
    "primary_endpoint": "single scalar or precisely specified statistic",
    "unit_of_analysis": "task / seed / independent episode",
    "denominator": "number and independence model",
    "direction": "larger_is_better / smaller_is_better / equals_predicate",
    "success_threshold": "numeric value with units or exact predicate",
    "minimum_meaningful_effect": "numeric value, units and rationale"
  },
  "design": {
    "task_distribution": "frozen generator/distribution and range",
    "policy_inputs_allowed": "the exact inference-time observables",
    "protected_oracle": "what must not be exposed",
    "calibration_data": "separate source or NONE",
    "evaluation_data": "withheld source/commitment or UNKNOWN",
    "resources": "matched trials, updates, tokens, wall time or effects as relevant",
    "stop_rule": "frozen rule and invalid-run handling"
  },
  "comparators": {
    "primary_strong_baseline": "name / method / revision",
    "baseline_selection_reason": "closest viable prior-art rival under same constraints",
    "omitted_competitors": "names and pre-outcome exclusion reasons",
    "trivial_floor_controls": "known weak or non-learning floors, if any"
  },
  "feasibility": {
    "contrast_bound": "math or independent-calibration evidence plus provenance",
    "forecast_method": "analytic / independent simulation / none",
    "forecast_input_provenance": "non-outcome inputs only",
    "planned_precision": "variance / paired-SE / justified unknown",
    "assumptions_and_failure_modes": "explicit list"
  },
  "threat_scope": {
    "tested_mechanism_or_attack": "explicit finite shapes or NA",
    "positive_control": "must pass a valid case",
    "negative_control": "must detect a known invalid case"
  }
}
```

For purely structural tests, `comparators` and inferential `planned_precision` can be marked `NOT_APPLICABLE_STRUCTURAL`, never represented as zero variance in a population. For other declared study types, `UNKNOWN` must remain visible. A developer may not quietly convert `NOT_APPLICABLE` into a performance claim.

## 4. Methodological gates (pre-outcome only for PROSPECTIVE decisions)

**G0 — Registration / data lineage.** Verify specific source revision, protocol bytes and acceptance criteria can be inspected; unknown paths/hashes or stale/rewritable evaluators are declared. Register protocol, task family, denominators, primary comparison and stop rule **before the experiment**. No test labels, measured held-out effects, hidden answer tables or later experiments can feed the prospective classification. Prior public *study results* may be reviewed as prior art but not re-labeled prospective for that same completed study.

**G1 — Construct and estimand.** Define what inference can be made: structural correctness, descriptive behavior, or estimated performance contrast. A deterministic planted counterexample is **not** a population failure-rate estimate. A simulated task can be an appropriate unit test without being a scientific generalization. Primary endpoint and denominator must actually measure the stated contrast.

**G2 — Identifiability / possible discrimination.** Document worst/best reachable outcome boundaries *under exactly specified budgets and observables* and the preregistered success margin; distinguish ceiling/floor from observed saturation. A clairvoyant true-label oracle is allowed only as an **optimistic impossibility bound**: if even that bound cannot meet a threshold, it may justify a negative feasibility flag subject to correct math. If it *can* meet the threshold, that says **nothing** about an implementable policy. A learned/feasible stopping policy must use only approved inference-time inputs and separate calibration/training data. No universal exclusion of chance-level tasks, no 2-binomial-SD rule, and no retroactive endpoint changes.

**G3 — Strongest relevant comparator.** Identify the strongest credible *available* prior-art baseline within the same capability class, compute budget and objective. Document its provenance, tuning rules and any exclusions before running. Non-learning baselines can be sanity floors but are not sufficient evidence for a comparative learning advantage when stronger learners are available. "Strongest" is contextual rather than globally provable; unresolved plausible rivals produce `INSUFFICIENT_INFORMATION` for superiority claims. A specifically scoped software-demonstration claim can instead be a `DEMONSTRATION`.

**G4 — Forecastability / information value.** Ask which of the contrasted results are already mathematically implied by the assumptions, and whether the result would update belief beyond prior art. Document forecasts *before* experiment output: derivation or clearly separated pilot/synthetic draws, parameters, model uncertainty, expected effect distribution and probability of crossing the declared threshold, including predictions for a credible null and alternative. A policy might fail despite strong theory due to an implementation bug; that possibility makes it a useful correctness test, **not** necessarily a new performance discovery. No uncalibrated "99% predicted" rule may certify scientific triviality on its own. A fully analytic/determined contrast, or an advertised advantage against only trivial floors, is `DEMONSTRATION` as that specific contribution is framed. If no defensible pre-outcome forecast exists, keep `UNCERTAIN` or `INSUFFICIENT_INFORMATION`.

**G5 — Precision and resource comparability.** Give independent units, paired variance/uncertainty from *disjoint* calibration or credible analytic arguments, expected minimum detectable effect, multiple comparisons handling where applicable, equal substantive action/inference/training budget, timing and cost measurement plan. More seeds do not rescue a saturated metric, leaked label oracle, or trivial comparator. For rate estimation, report confidence intervals/limits and sampling frame; don't equate count with probability without sampling assumptions.

**G6 — Structural controls and threat coverage.** Structural tests must name exactly which threats/cases they cover, with both an accepted valid case and a deliberately invalid case. A passing test covers only registered cases, not an unseen attack family. EPV's forged-dissent fixture does not imply protection from anchor-registry substitution. A broad claim not supported by the enumerated fixtures is `CONTRACT_INVALID` until narrowed.

**G7 — Final disposition and auditability.** Emit one of the six labels with gate-by-gate `PASS / FAIL / UNKNOWN / NOT_APPLICABLE` diagnostics, exact reason codes, source revision and a record of the owner's authorization status. A reviewed checker output is not permission to execute. If gate disagreement cannot be resolved after the declared review budget, record `CONTESTED` and stop rather than let either AI relabel the claim.

## 5. Historical diagnostic fixtures (NOT preregistered scientific reassessments)

These are **visible** development fixtures, not hidden acceptance tests. Read actual protocols/raw records before finalizing expected classifications. Past outcomes and negative findings must remain unchanged. Historical classifications describe the **claim being marketed**, not whether code ran correctly.

| Fixture and interpretation being tested | Expected precheck disposition / flag | Reason / limitation |
|---|---|---|
| VERITAS ORIGIN EXP-003-P0, "all policies solved the task" as discriminatory completion-rate endpoint | `NONDISCRIMINATING_ENDPOINT`, `RETROSPECTIVE_DIAGNOSTIC` | Observed 12/12 for each baseline saturates the original completion endpoint; **do not pretend** a prospective guarantee was established before those observations. Post-hoc probe counts remain descriptive. |
| VERITAS ORIGIN EXP-002, "UCB1 demonstrates a novel/relevant comparative learning advantage" against fixed-medium and uniform random | `DEMONSTRATION` | Fixed-medium and uniform random expect 50/100 given p=.2/.5/.8; strong learning competitor absent. UCB1's **exact finite-horizon score is not fixed** by that arithmetic. Narrow preregistered threshold remains MET and original results remain intact. |
| Sovereign Veritas RK-1, fresh-ID retry gives two effects vs a deduplication control | `STRUCTURAL_TEST` with anti-vacuity controls and limited scope | A known specific retry/error case is a valid deterministic behavioral contrast, *not* a population effect rate or production assurance. |
| VERITAS ORIGIN ITC-001 H2, claims implementable adaptive-stopping headroom of >=+1 pp from post-hoc perfect-depth label oracle | `INSUFFICIENT_INFORMATION`, `ORACLE_LEAKAGE_TO_HEADROOM_ARGUMENT`, `RETROSPECTIVE_DIAGNOSTIC` | Registered oracle D1 HELD; its +4.358 pp is true-label-aware hindsight. Parity8 exclusion is post-hoc. Neither feasible policy headroom nor its absence has been proved. H2 remains NOT_SUPPORTED in original study. |
| VERITAS ORIGIN EPV-001, 512/512 poisoned-anchor episodes advertised as estimated real-world failure rate | `CONTRACT_INVALID` **for that rate claim**; if correctly scoped as a planted synthetic attack, `STRUCTURAL_TEST` and `THREAT_COVERAGE_LIMITED` | All 512 cases intentionally contain the same constructed failure mechanism. This is a valid invariant/counterexample, not a population sampling rate. |
| VERITAS ORIGIN ASP-001, mean MSE spread .0064 alone used to claim mathematical impossibility of detecting a difference | `INSUFFICIENT_INFORMATION` | Need paired uncertainty, practical margin and comparison controls; small observed spread alone doesn't prove intrinsic nondiscrimination. Original regulator H1 remains NOT_SUPPORTED. |

**Caution:** In EXP-003-P0, the 12/12 saturation is evidence *after the experiment*, not valid input for an originally prospective prediction. Test both: (a) a retrospective reasoned diagnostic, and (b) an insufficient-information prospective design with withheld task outcomes if no legitimate bound was available.

## 6. Prospective, withheld and mutation controls for the *precheck itself*

The test author (Claude or another authorized reviewer) must work from **this owner's frozen spec** on a separate branch, without reading the eventual checker implementation. Tests should cover all dispositions with exact expected primary label, required reason code, and counterfactual mutation, including these failure classes:

- A valid **nontrivial** comparative scenario with matched strong rival and a preregistered genuinely uncertain expected sign must be `READY_FOR_COMPARISON`; avoid an always-block checker.
- A valid bounded structural good/bad pair must be `STRUCTURAL_TEST`; test a mutation removing the good control and another broadening the untested threat scope.
- A mathematically impossible registered margin under an admissible absolute upper bound must be `NONDISCRIMINATING_ENDPOINT`; a merely saturated small pilot should not automatically be classed as impossible prospectively.
- A known deterministic result with a weak/trivial comparator must be `DEMONSTRATION`, not `READY_FOR_COMPARISON`.
- A label-aware hindsight oracle repackaged as feasible performance must be `INSUFFICIENT_INFORMATION` (or `CONTRACT_INVALID` if the contract explicitly misrepresents access).
- Missing baseline evidence, sample unit, or uncertain power must not silently pass; categorize `CONTRACT_INVALID` for malformed requirements and `INSUFFICIENT_INFORMATION` for honest unresolved feasibility.
- A study with an actually strong rival but nontrivial uncertain outcome must **not** be auto-rejected just because there is established prior art.
- An invalid-review mutant that marks everything `READY_FOR_COMPARISON`, and an always-refuse mutant that marks nothing ready, must **both** fail.
- A retrospective relabeling mutation that changes historic hypothesis statuses or silently drops parity8 must fail.

**Holdout procedure:** Before checker implementation begins, Claude proposes a prospective `TEST_PLAN` and a hidden-case digest manifest whose SHA-256 commitments are posted with source provenance to PR #16. Holdout *contents* are supplied after checker implementation is frozen, under Chad's custody; a public GitHub hash alone does not prevent an AI from guessing or leaking cases. Include at least one case from outside the known historical experiment family to test overfitting. Report the predeclared case count, pass/fail, category confusion matrix, reason-code checks and all mutations. Count abstention/UNKNOWN cases honestly; a high percentage of `INSUFFICIENT_INFORMATION` is not proof of quality. Only **one held-out acceptance run**, with every case and all mismatches preserved, under a separately authorized execution decision.

## 7. Two-phase freeze and stopping contract

**Phase A — design only (NOW):**
1. ChatGPT commits this **draft** on its own coordination branch with a draft PR targeting `coordination/ai-biology-research-exchange`, and links it from PR #16.
2. Chad reads it and either requests revisions **before freeze** or explicitly approves its exact **full commit SHA + content SHA-256**.
3. Chad records `SPEC_FROZEN` with the immutable path and both hashes in PR #16. A mere successful GitHub commit or review by both AIs **is not freeze approval**.
4. Any changes after freeze require a new version, amendment rationale and **new owner approval**. Never overwrite the frozen file.

**Phase B — test authoring only (AFTER OWNER FREEZE):**
5. Claude authors **separate** versioned tests and a withheld-case digest manifest; no checker code or science experiments are authorized as part of this stage.
6. Chad approves the test manifest and decides whether a subsequent checker implementation and single held-out acceptance run may begin; that work requires a further explicit scope decision.
7. On unresolved disputes after at most **two response rounds per disputed rule**, log `CONTESTED` / `STOPPED_CONTESTED` and ask Chad rather than loop forever.

**Stop now when:** this spec is committed in a draft PR, the link is posted to PR #16, and the owner is told that review/hash freeze remains outstanding. No experiments, CI/benchmark runs, branch protections, merges or security reviews are silently performed.

## 8. Specific questions for Chad and Claude

- Does the priority ordering misclassify a contract that contains *both* a legitimate structural invariant and an unsupported population-rate claim? Should those instead be separated into distinct study IDs? (Proposed answer: yes.)
- Is `DEMONSTRATION` reserved for the stated claim of novelty/comparison, leaving deterministic correctness verification useful as `STRUCTURAL_TEST`? Avoid using "known" as an insult or rejecting replication.
- What smallest prospectively defined, **attainable** nontrivial positive fixture can test `READY_FOR_COMPARISON` without peeking at outcome labels?
- Is the exact owner freeze procedure sufficient to stop both agents from modifying the acceptance contract? It does not stop owner rewrite or shared account compromise; state that limitation.

**Status at publication:** DRAFT ONLY. Source read; no checker written or executed; no new empirical claim.
