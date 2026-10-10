# DPC-001 v0.2 — freeze CANDIDATE record (NOT FROZEN)

```yaml
artefact: dpc001_v02/FREEZE_CANDIDATE
by: Claude (Opus 5.5)          # prepared at Chad Holland's direction 2026-10-09; Chad has not reviewed it line by line
state: FREEZE_CANDIDATE / NOT_FROZEN / NOT_VALIDATED
frozen_target_commit: bc43adf3b51633dfb831ce420afe90ec3ac04ab7   # this record lives in a later commit and changes no frozen file
next: "ChatGPT audits this record; Chad confirms D1–D6 in his own words and authorizes (or rejects) the freeze"
```

## 1. Exact bytes proposed for freezing

SHA-256 of each file as it exists at `bc43adf` (computed with `git show bc43adf:<path> | sha256sum`). The suite was rerun from a clean `git archive bc43adf` extract (Python 3.13.15, `-I`).

| File (`coordination/dpc001_v02/`) | SHA-256 | Role |
|---|---|---|
| `SPEC_V02_DRAFT.md` | `fce85463ebbb552b0bf44a4a9bb90d5851101b378d31f91a6bb7786405737186` | specification (amends frozen v0.1 `d055010`) |
| `checker.py` | `f2746a43e1e7360f645be912e552a84e53eca950d07d93d98adbc4d087eeca34` | implementation under test |
| `run_acceptance.py` | `84a918c2f50849e7b4ec8384ec88800f3aed85399684673a21efddae4a39b6e1` | harness (identical to PR #20) |
| `visible_cases_v02.json` | `4b7cd3ab65e829e4b0d56f4dcd94663f6e0af24039ed8f8742bb810754a98721` | visible development cases |
| `prose_invariance.py` | `c7387575c1f405d86540903b0dcab6634762e29196afc7a8d5f4fd2a6115aa65` | prose-invariance test |
| `build_cases_v02.py` | `d782f361f5d8c1191b6caa1d61c24eb0dbe5fd9e55b6b63916a79015c2cdc2e4` | generator for the visible cases |

The **spec and checker** are the frozen objects. Harness, cases and invariance test are recorded so the run can be reproduced exactly.

Output from the clean extract, pasted:
```
VERDICT  55 of 55 cases as expected (checker checker.py:classify)
VERDICT  110 of 110 rewrites kept the label
```

## 2. Rule decisions D1–D6 (spec §7)

| # | Rule | Both AIs recommend | Chad's decision |
|---|---|---|---|
| D1 | READY only for `COMPARATIVE_EFFECT` | approve | **PENDING: Chad's own confirmation** |
| D2 | analytically predetermined novel advantage → DEMONSTRATION | approve | **PENDING** |
| D3 | constructed, non-generalized rate → INSUFFICIENT. *Limitation: this does not say the observations are invalid; a correctly scoped claim belongs under STRUCTURAL.* | approve with limitation | **PENDING** |
| D4 | READY and ND need `ATTESTED` plus a bound artifact; a blocked ND candidate → INSUFFICIENT. *Limitation: attestation and artifact links are self-declared, with no reviewer identity or signature, so they are not verified provenance.* | approve with limitation | **PENDING** |
| D5 | strict facts schema plus range invariants | approve | **PENDING** |
| D6 | prospective review using observed outcomes → INVALID | approve | **PENDING** |

ChatGPT relayed these as approved. Under the project rule, owner decisions are recorded only from Chad directly, so they stay PENDING until he confirms here or to Claude.

## 3. Known limitations carried into any result
- The checker trusts declared facts. It does not authenticate artifacts, attestations or provenance, and a fabricated link passes.
- Prose-invariance (110/110) shows only that the checker ignores prose. It says nothing about whether a contract is admissible.
- All 55 visible cases and the checker share one author (Claude), so the V01–V20 labels match v0.1 by construction.
- ChatGPT has read this checker, so a ChatGPT-written blind set tests it against an informed adversary. It is not independent of the two-AI process.
- Enum boundaries (for example `STRONG_PRIOR_ART`, `ENUMERATED`) are per-study human judgements.

## 4. Negative findings preserved
- **v0.1 checker (PR #24, ChatGPT):** visible 20/20, but paraphrase round 1 kept 2/8. After phrase patches, round 1 kept 8/8 and round 2 kept 1/8. Prose-invariance kept 19/40. Phrase-matching overfits. Kept as a negative result.
- **v0.1 withheld cases** (Claude-authored, sha256 `abb0120e…`, held by Chad): retired, never run. They can't blind-test a Claude-written checker.
- **Defects found and fixed in v0.2 before freeze**, each registered with a failing test first:
  - the D4 ND gate (A17: 52/53 → 53/53);
  - ND precedence fall-through (A18: 54/55 → 55/55).

## 5. What a freeze would and would not authorize
- **Would:** fix the two frozen files above. Any later change needs a new version and Chad's approval.
- **Would not:** authorize writing, running or merging anything. The blind evaluation needs separate steps:
  1. ChatGPT pre-registers a plan and case digests (contents to Chad only).
  2. Chad authorizes a single run against these exact bytes.
  3. Every result is kept.
