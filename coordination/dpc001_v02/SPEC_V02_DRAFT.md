# DPC-001 v0.2 — typed-facts amendment (DRAFT, NOT FROZEN)

**Status:** `DRAFT_FOR_OWNER_REVIEW / NOT_FROZEN / NOT_VALIDATED`. It amends the frozen v0.1 spec (`coordination/specs/DPC001_DISCRIMINATION_PRECHECK_DRAFT.md`, commit `d05501013c7b2d0c602893e44d157620b55f12ff`, sha256 `c02a1daa…cf9`). The v0.1 file is **not** edited. Everything in v0.1 still applies except the points below.
**Author:** Claude (Opus 5.5), 2026-10-09, at Chad Holland's direction. Not reviewed line by line. ChatGPT is invited to critique it.
**Why:** v0.1 §3 calls its schema "illustrative". All the decisive facts were free text. The first checker built on it (PR #24) matched phrases. It scored 20/20 on the visible cases but kept 1 of 8 labels under meaning-preserving rewording (paraphrase round 2, `ce3b2f3`). Patching phrases did not converge. This amendment moves the facts that decide the label into typed fields.

## 1. What changes

1. `schema` becomes `"dpc-study-v0.2"`.
2. A required `facts` block is added. Its fields are booleans, enums or numbers. Unknown numbers are the string `"UNKNOWN"` and structural non-applicability is `"NOT_APPLICABLE"`, never `null`.
3. The v0.1 prose fields stay **required and non-empty**, because people read them. A checker **must not** use their wording to decide a label. This is tested by `prose_invariance.py`: every prose field is rewritten, and every label must stay the same.
4. Missing or ill-typed facts give `CONTRACT_INVALID` (`CONTRACT_MALFORMED`). Nothing defaults to READY.
5. *(Added after ChatGPT's review, PR #25 comment 6091333519.)* The `facts` block is **strict**: unknown sections or keys are rejected. Prose sections stay lenient.
6. *(Same review.)* Range invariants:
   - `max_abs_contrast >= 0`;
   - `threshold > 0`, meaning the magnitude of the required margin in the hypothesis's own direction, so there is no sign to absolutize;
   - `mde > 0` and `min_effect > 0`;
   - `independent_units >= 1`.
   NaN and infinity are rejected. `bound.units` and `precision.units` are required. Only numbers inside the same section are compared, so they share units by definition.
7. *(Same review.)* An `attestation` block is added: `status` is `ATTESTED / UNATTESTED / CONTESTED`, and `bound_artifact` is a pinned reference or `NONE`.
   - `CONTESTED` gives `INSUFFICIENT_INFORMATION` (`FACTS_CONTRADICTION_UNRESOLVED`).
   - `READY` requires `ATTESTED` and a non-`NONE` bound artifact.
   - `NONDISCRIMINATING_ENDPOINT` requires `ATTESTED` **and** a non-`NONE` bound artifact; otherwise the result is INSUFFICIENT (`FACTS_UNATTESTED` and/or `BOUND_NOT_CORROBORATED`). *(The code was aligned to this after ChatGPT's follow-up, comment 6091374834. At 92a9879 the ND branch checked only the artifact.)*
   - These are **declared** too. `ATTESTED` self-certifies: it carries no reviewer identity or signature. The checker can't tell a real attestation or proof from a fabricated one (§4). It must not be described as verified provenance.

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
| `bound.units`, `precision.units` | non-empty string | G2, G5 |
| `attestation.status` | `ATTESTED / UNATTESTED / CONTESTED` | G0, G7 |
| `attestation.bound_artifact` | pinned path@revision, or `NONE` | G2 |

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

- **Passing prose-invariance proves the checker ignores prose, nothing more** (ChatGPT's point 1). It does not show that a contract is admissible. Contradictions between prose and facts are invisible to the checker by design and must be caught by attestation.
- **Attestation and bound artifacts are declarations.** A fabricated attestation or proof link passes. A second AI agreeing is not independent evidence. READY becomes operationally usable only after a human (Chad, or an outside reviewer) has checked the attested artifacts.
- **The facts can be false.** The checker verifies that facts are present, well typed and consistent with each other. It does not verify them against the prose or the world. The hard judgement moves to whoever fills in `facts`. Proposed control (not built): the study author fills in `facts`, and a second reviewer (the other AI, or Chad) attests them field by field. Any disagreement goes to `CONTESTED` (v0.1 §7). This is a human/AI review step, not a checker feature.
- **Enum boundaries are judgements.** Examples: when a baseline counts as `STRONG_PRIOR_ART`, or a scope as `ENUMERATED`. They are made once, visibly, per study, instead of being inferred from wording at every run.
- **Two decisions are mine and open to challenge:** READY requires a `COMPARATIVE_EFFECT` claim, and a constructed rate that is *not* generalized gives INSUFFICIENT rather than INVALID.

## 5. Tests and evidence in this directory (all run, outputs in README)

- `visible_cases_v02.json`: the 20 v0.1 visible cases with unchanged prose and labels, plus a `facts` block encoding what each prose declares. It adds 16 one-fact flips on the READY case (F01–F16) and 16 adversarial typed-fact cases (A01–A16) from ChatGPT's review: nested types, NaN/inf, out-of-range numbers, contradictory flags, unknown keys, and missing attestation or bound artifacts.
- `prose_invariance.py`: rewrites all prose two ways, and every label must hold.
- The four trivial mutants from v0.1's harness must fail.

## 6. Custody and next steps

- The six v0.1 withheld cases are in v0.1 format and were written by Claude, who wrote this checker. They **cannot** be a blind test of it. They stay committed by hash and unused.
- A v0.2 blind test needs **new withheld cases written by ChatGPT**, which Claude never sees. Chad holds them and releases them once for one run against a frozen checker commit.
- Chad freezes or rejects this amendment. Until then it is a draft, and nothing here authorizes running anything.

## 7. Owner decisions: what v0.2 changes relative to v0.1 (ChatGPT's point 4)

The 20 v0.1 visible cases keep their expected labels. **That is by construction, not confirmation.** Claude encoded each case's facts knowing its expected label. Rule changes that could give a different label on *other* contracts:

| # | Change | v0.1 behaviour (spec text) | v0.2 behaviour | Needs Chad's approval |
|---|---|---|---|---|
| D1 | READY limited to `COMPARATIVE_EFFECT` | §2 READY "names strong relevant baselines and estimates an attainable … contrast", implicitly comparative | a `DESCRIPTIVE_RATE` contract can never be READY and gets INSUFFICIENT | yes |
| D2 | `ANALYTICALLY_PREDICTABLE` plus `NOVEL_ADVANTAGE` gives DEMONSTRATION | §4 G4 "a fully analytic/determined contrast … is DEMONSTRATION as that specific contribution is framed" | same, now mechanical | confirm reading |
| D3 | constructed rate *not* generalized gives INSUFFICIENT | §5 row 5 covers only the generalized case (INVALID) | INSUFFICIENT; a correctly scoped one should be filed as STRUCTURAL | yes |
| D4 | attestation gate on READY and NONDISCRIMINATING | not in v0.1 | READY or ND without attestation or a bound artifact becomes INSUFFICIENT | yes |
| D5 | strict facts schema plus range invariants | v0.1 §3 "illustrative" | malformed facts give INVALID | yes |
| D6 | `OBSERVED_OUTCOME` bound in a PROSPECTIVE review gives INVALID | §4 G0 "No … measured held-out effects … can feed the prospective classification" | mechanical | confirm reading |

## 8. Order of work before any blind test (ChatGPT's point 5, agreed)

1. Chad accepts, rejects or amends D1–D6.
2. Chad freezes the exact bytes of this spec and the checker.
3. ChatGPT, as test author, pre-registers a test plan and posts case digests only. Contents go to Chad, never to GitHub or Claude.
4. Chad authorizes one blind run.
Two-AI process limits stay stated: ChatGPT has seen this checker and Claude's visible cases, so that run tests against an adversary who knows the code, not against the world.
