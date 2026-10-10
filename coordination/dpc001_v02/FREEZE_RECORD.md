# DPC-001 v0.2 — FREEZE RECORD

```yaml
artefact: dpc001_v02/FREEZE_RECORD
state: SPEC_AND_CHECKER_FROZEN / NOT_VALIDATED / BLIND_TEST_NOT_AUTHORIZED
frozen_commit: bc43adf3b51633dfb831ce420afe90ec3ac04ab7
frozen_files:
  coordination/dpc001_v02/SPEC_V02_DRAFT.md: fce85463ebbb552b0bf44a4a9bb90d5851101b378d31f91a6bb7786405737186
  coordination/dpc001_v02/checker.py:        f2746a43e1e7360f645be912e552a84e53eca950d07d93d98adbc4d087eeca34
owner_decision: "Chad Holland, directly to Claude, 2026-10-09 19:32 CDT: D1–D6 approved and freeze of bc43adf authorized"
recorded_by: Claude (Opus 5.5)   # Chad gave the decision; he has not reviewed this file line by line
```

## Decisions (spec §7), approved by Chad Holland on 2026-10-09
| # | Rule | Decision |
|---|---|---|
| D1 | READY only for `COMPARATIVE_EFFECT` | APPROVED |
| D2 | analytically predetermined novel advantage → DEMONSTRATION | APPROVED |
| D3 | constructed, non-generalized rate → INSUFFICIENT | APPROVED, with the limitation that INSUFFICIENT does not declare the observations invalid; a correctly scoped claim belongs under STRUCTURAL |
| D4 | READY and ND require `ATTESTED` plus a bound artifact; a blocked ND candidate → INSUFFICIENT | APPROVED, with the limitation that attestation and artifact links are self-declared (no reviewer identity or signature) and are not verified provenance |
| D5 | strict facts schema plus range invariants | APPROVED |
| D6 | prospective review using observed outcomes → INVALID | APPROVED |

## Verification at freeze time (Claude-run)
- The SHA-256 of both frozen files was computed from `git show bc43adf…:<path>` and matched the values above. The same files at branch head `78a2a90` are byte-identical.
- From a clean `git archive bc43adf` extract (Python 3.13.15, `-I`), pasted:
  ```
  VERDICT  55 of 55 cases as expected (checker checker.py:classify)
  VERDICT  110 of 110 rewrites kept the label
  ```
- **Independent check, not yet done:** ChatGPT has not recomputed these digests (its note `vo/chatgpt/012`). Chad can recompute them on any machine:
  ```
  git show bc43adf:coordination/dpc001_v02/checker.py | sha256sum
  ```

## Freeze rules
1. The two frozen files are never edited. Any change is a new version (v0.3) with its own spec, rationale and owner approval.
2. Later commits on this branch may add records and tests. A commit that alters either frozen file's bytes voids this record.
3. The blind evaluation runs against these exact bytes, checked by digest at run time. Anything else is not the frozen object.

## Carried forward unchanged
Limitations (§3) and negative findings (§4) in `FREEZE_CANDIDATE.md` apply in full:
- v0.1 phrase-matching failure;
- retired v0.1 withheld cases;
- two v0.2 defects fixed before freeze;
- self-declared facts;
- single-author visible tests;
- an informed-adversary blind set.

## Not authorized by this freeze
Writing, sharing or running blind tests; merging PR #25; any claim of validation. Each next step needs its own step and owner authorization:
1. ChatGPT pre-registers a test plan and case digests, with contents to Chad only.
2. Chad authorizes one run.
3. Every result is kept.
