# DPC-001 v0.2 — typed-facts amendment (DRAFT, NOT FROZEN)

**Status:** `DRAFT_FOR_OWNER_REVIEW / NOT_FROZEN / NOT_VALIDATED`. It amends the frozen v0.1 spec (`coordination/specs/DPC001_DISCRIMINATION_PRECHECK_DRAFT.md`, commit `d05501013c7b2d0c602893e44d157620b55f12ff`, sha256 `c02a1daa…cf9`). The v0.1 file is **not** edited. Everything in v0.1 still applies except the points below.
**Author:** Claude (Opus 5.5), 2026-10-09, at Chad Holland's direction. Not reviewed line by line. ChatGPT is invited to critique it.
**Why:** v0.1 §3 calls its schema "illustrative". All the decisive facts were free text. The first checker built on it (PR #24) matched phrases. It scored 20/20 on the visible cases but kept 1 of 8 labels under meaning-preserving rewording (paraphrase round 2, `ce3b2f3`). Patching phrases did not converge. This amendment moves the facts that decide the label into typed fields.

## 1. What changes

1. `schema` becomes `"dpc-study-v0.2"`.
2. A required `facts` block is added. Its fields are booleans, enums or numbers. Unknown numbers are the string `"UNKNOWN"` and structural non-applicability is `"NOT_APPLICABLE"`, never `null`.
3. The v0.1 prose fields stay **required and non-empty**, because people read them. A checker **must not** use their wording to decide a label. This is tested by `prose_invariance.py`: every prose field is rewritten, and every label must stay the same.
4. Missing or ill-typed facts give `CONTRACT_INVALID` (`CONTRACT_MALFORMED`). Nothing defaults to READY.

## 2. The `facts` block and the gate each field serves

| Section.field | Type | Gate (v0.1 §4) |
|---|---|---|
| `registration.relabels_registered_outcome` | bool | G0 |
| `registration.outcome_informed_design_choice` | bool | G0 (any design choice made after seeing outcomes, prospective only) |
| `construct.structural_scope` | `NOT_STRUCTURAL / ENUMERATED / BROAD` | G6 |
| `construct.structural_includes_rate_claim` | bool | G1 |
| `construct.rate_population` | `NOT_A_RATE_CLAIM / SAMPLED_FROM_TARGET / CONSTRUCTED_NOT_SAMPLED` | G1 |
| `construct.rate_generalized_beyond_sample` | bool | G1 |
| `oracle.policy_inputs_include_eval_labels` | bool | G2 |
| `oracle.label_oracle_role` | `NONE / OPTIMISTIC_BOUND_ONLY / USED_AS_HEADROOM_EVIDENCE / CLAIMED_ACHIEVABLE` | G2 |
| `bound.kind` | `ANALYTIC / INDEPENDENT_CALIBRATION / OBSERVED_PILOT / OBSERVED_OUTCOME / NONE` | G0, G2 |
| `bound.max_abs_contrast`, `bound.threshold` | number or `UNKNOWN`/`NOT_APPLICABLE`, same units | G2 |
| `comparator.strength` | `STRONG_PRIOR_ART / TRIVIAL_FLOOR_ONLY / UNRESOLVED / NOT_APPLICABLE_STRUCTURAL` | G3 |
| `comparator.contribution` | `NOVEL_ADVANTAGE / REPLICATION / CORRECTNESS / DEMONSTRATION` | G3, G4 |
| `forecast.status` | `ANALYTICALLY_PREDICTABLE / PREDECLARED_FORECAST / UNCERTAIN / UNAVAILABLE / NOT_APPLICABLE` | G4 |
| `precision.status`, `mde`, `min_effect`, `calibration_disjoint`, `independent_units` | enum / number / `YES·NO·UNKNOWN·NOT_APPLICABLE` / count | G5 |
| `controls.positive`, `controls.negative` | bool | G6 |

## 3. Decision procedure (v0.1 §2 precedence, made exact)

1. **CONTRACT_INVALID** applies if any of the following hold:
   - the contract is malformed;
   - it relabels a registered outcome;
   - it is a prospective review that uses outcome-informed design or an `OBSERVED_OUTCOME` bound;
   - it is a structural claim that includes a rate, has `BROAD` scope or lacks a control;
   - its structural facts don't match a non-structural claim kind;
   - it is a constructed rate generalized beyond its sample;
   - the policy inputs include evaluation labels, or the oracle is `CLAIMED_ACHIEVABLE`.
2. **STRUCTURAL_TEST** is any remaining structural claim. It always carries `THREAT_COVERAGE_LIMITED`.
3. **NONDISCRIMINATING_ENDPOINT** applies when the bound is `ANALYTIC` or `INDEPENDENT_CALIBRATION` (or `OBSERVED_OUTCOME` in a retrospective diagnostic), both numbers are present, and `|threshold| > max_abs_contrast`.
4. **DEMONSTRATION** applies when the contribution is `NOVEL_ADVANTAGE` and either the comparator is only `TRIVIAL_FLOOR_ONLY` or the forecast is `ANALYTICALLY_PREDICTABLE`. It also applies when the contribution is declared `DEMONSTRATION`.
5. **INSUFFICIENT_INFORMATION** applies if any readiness condition is unmet. Every unmet condition is listed:
   - the oracle is used as headroom evidence;
   - the review is retrospective;
   - the claim is not comparative;
   - there is no `ANALYTIC`/`INDEPENDENT_CALIBRATION` bound;
   - the comparator is not `STRONG_PRIOR_ART`;
   - the forecast is not `PREDECLARED_FORECAST`;
   - precision is not `ESTIMATED`;
   - calibration is not `YES` disjoint;
   - there are fewer than 2 independent units;
   - `mde > min_effect`, or either is unknown.
6. **READY_FOR_COMPARISON** applies only when none of the above fire.

## 4. What this does not solve (stated, not hidden)

- **The facts can be false.** The checker verifies that facts are present, well typed and consistent with each other. It does not verify them against the prose or the world. The hard judgement moves to whoever fills in `facts`. Proposed control (not built): the study author fills in `facts`, and a second reviewer (the other AI, or Chad) attests them field by field. Any disagreement goes to `CONTESTED` (v0.1 §7). This is a human/AI review step, not a checker feature.
- **Enum boundaries are judgements.** Examples: when a baseline counts as `STRONG_PRIOR_ART`, or a scope as `ENUMERATED`. They are made once, visibly, per study, instead of being inferred from wording at every run.
- **Two decisions are mine and open to challenge:** READY requires a `COMPARATIVE_EFFECT` claim, and a constructed rate that is *not* generalized gives INSUFFICIENT rather than INVALID.

## 5. Tests and evidence in this directory (all run, outputs in README)

- `visible_cases_v02.json`: the 20 v0.1 visible cases with unchanged prose and labels, plus a `facts` block encoding what each prose declares. It adds 16 one-fact flips on the READY case (F01–F16).
- `prose_invariance.py`: rewrites all prose two ways, and every label must hold.
- The four trivial mutants from v0.1's harness must fail.

## 6. Custody and next steps

- The six v0.1 withheld cases are in v0.1 format and were written by Claude, who wrote this checker. They **cannot** be a blind test of it. They stay committed by hash and unused.
- A v0.2 blind test needs **new withheld cases written by ChatGPT**, which Claude never sees. Chad holds them and releases them once for one run against a frozen checker commit.
- Chad freezes or rejects this amendment. Until then it is a draft, and nothing here authorizes running anything.
