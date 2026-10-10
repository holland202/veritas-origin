# DRAFT: public "try to break DPC-001 v0.2" challenge (NOT PUBLISHED)

**State: DRAFT_FOR_OWNER_AND_CHATGPT_REVIEW. Nothing here is posted, and README.md is not edited.** Drafted 2026-10-09 by Claude (Opus 5.5) at Chad Holland's direction. Chad has not reviewed it line by line. Publishing the issue and adding the README section each need Chad's direct authorization.

The reproduction command below must be rerun from a clean checkout at the moment of publishing. It was last run by Claude from a fresh `git clone` at `bc43adf` (Python 3.13, Linux container). Pasted output:
```
f2746a43e1e7360f645be912e552a84e53eca950d07d93d98adbc4d087eeca34  coordination/dpc001_v02/checker.py
fce85463ebbb552b0bf44a4a9bb90d5851101b378d31f91a6bb7786405737186  coordination/dpc001_v02/SPEC_V02_DRAFT.md
VERDICT  55 of 55 cases as expected (checker checker.py:classify)
```
The submission flow (a second case file holding the example `X01` below) was also run: `VERDICT  56 of 56`, exit 0.

---

## Part A: issue text (to be posted as a GitHub issue)

### Title
Try to break DPC-001 v0.2: find a study design it labels wrongly

### Body

**What this is.** DPC-001 is a small checker that reads a proposed study design (a JSON "contract") and gives it one of six labels before the study is run:
- `CONTRACT_INVALID`
- `STRUCTURAL_TEST`
- `NONDISCRIMINATING_ENDPOINT`
- `DEMONSTRATION`
- `INSUFFICIENT_INFORMATION`
- `READY_FOR_COMPARISON`

Version 0.2 is frozen at commit `bc43adf`. It decides only from a typed `facts` block, never from the wording of the prose. The rules are in [`SPEC_V02_DRAFT.md`](https://github.com/holland202/veritas-origin/blob/bc43adf3b51633dfb831ce420afe90ec3ac04ab7/coordination/dpc001_v02/SPEC_V02_DRAFT.md).

**Why we're asking.** Everything so far was built and tested by one person working with two AI systems:
- Claude wrote the checker and its 55 visible cases, and ran property tests on its own code. ChatGPT's audit lists the limits of those tests (PR #25, note 044).
- ChatGPT wrote the cases for two blind runs. It had read the checker, so those runs test against an informed adversary, not an independent one.

The blind runs, both run by the owner, are kept separately:
- run 1: **FAIL 23/24**, caused by a test-author error, still recorded as FAIL;
- run 2: **PASS 24/24**.

**None of this is independent validation.** We want a person outside the project to find where it's wrong.

**Reproduce in one command** (needs git and Python 3.10+; no installs):
```
git clone https://github.com/holland202/veritas-origin.git && cd veritas-origin && git checkout bc43adf && cd coordination/dpc001_v02 && python3 -I run_acceptance.py --checker checker.py:classify visible_cases_v02.json
```
Expected last line: `VERDICT  55 of 55 cases as expected (checker checker.py:classify)`.
Check that you have the frozen bytes:
```
sha256sum checker.py   # f2746a43e1e7360f645be912e552a84e53eca950d07d93d98adbc4d087eeca34
```

**Known weakness. Disclosed up front, so not a new finding.** The checker trusts the facts it is given. It does not open or verify the evidence a contract points to:
- a made-up `bound_artifact` reference is accepted;
- a false `ATTESTED` status is accepted;
- false facts in general are accepted.

For example, pointing V15's artifact at a file that doesn't exist still gives `READY_FOR_COMPARISON`. This is stated in spec §4. A fix would be a new version (v0.3), not a change to v0.2.

**What counts as a break (please send these):**

| # | Kind of violation | Example of what you'd show |
|---|---|---|
| 1 | **Wrong label under the spec's own rules.** For the facts given, the spec text requires label X and the checker returns Y | facts that meet a §3 INVALID rule but come back READY |
| 2 | **Crash or non-label output.** Any input that raises an error or returns something other than one of the six labels | a nested or odd-typed value that throws |
| 3 | **Wording changes the label.** Rewriting only prose fields, with `facts` unchanged, changes the label | two contracts identical except for prose, with different labels |
| 4 | **Nondeterminism.** The same input gives different labels across runs or machines | the input plus both outputs |
| 5 | **Spec contradiction.** Two rules in the spec require different labels for the same facts, so no checker could be correct | the facts and the two rule citations |

**What is expected behavior (please don't send these as breaks):**
- fake or unverifiable artifacts and attestations accepted, and false facts accepted (spec §4, disclosed above);
- disagreement with a rule that is applied as written, such as D1–D6 in `FREEZE_RECORD.md`. That is a design objection, which we also want, but please label it as one;
- disagreement with an enum boundary (e.g. what counts as `STRONG_PRIOR_ART`). These are per-study judgements by design.
- extra keys at the top level of the contract are ignored. Only the `facts` block is strict (spec §1.5). A contract can carry e.g. `"status": "VALIDATED"` at the top level and the label does not change, because the checker never reads it. A downstream reader might trust such a field, so this is a design objection worth making, but it is not a break of v0.2's spec. Gemini found it on 2026-10-09; see PR #25 note 047.

**How to submit.** Put your case in a file such as `my_cases.json`, as changes ("overrides") to the shared base contract in `visible_cases_v02.json`:
```json
{"cases": [
  {"id": "X01",
   "title": "example: fake artifact reference on the READY baseline (known weakness, NOT a break)",
   "spec": "SPEC_V02_DRAFT.md section 4",
   "expect": "READY_FOR_COMPARISON",
   "overrides": {"facts": {"attestation": {"bound_artifact": "nothing/real.txt@0000000"}}}}
]}
```
Run it beside the visible cases:
```
python3 -I run_acceptance.py --checker checker.py:classify visible_cases_v02.json my_cases.json
```
Set `expect` to the label **you say the spec requires**. A `FAIL` line on your case means the checker disagrees with you. Then comment on this issue with:
1. the case JSON;
2. the label you say the spec requires, and the spec section(s) that require it;
3. the checker's output line, pasted;
4. which kind of violation (1–5) it is, or "design objection".

**What happens to a report.** Every report is answered on this issue. A confirmed break is recorded as a failure of v0.2, credited to you by name (or as you prefer), and kept: v0.2 is never edited. Fixes go into a new version with its own spec and tests. We'll say plainly when we think a report is expected behavior, and why. You're free to disagree, and that disagreement stays on the issue too.

**Provenance.** The checker, spec and visible tests were written by Claude (Anthropic) under the direction of Chad Holland, the repository owner, who approved the rules and the freeze. ChatGPT (OpenAI) reviewed them and wrote the blind cases. Chad did not review the code line by line.

---

## Part B: README section (to be added under the DPC-001 status section)

```markdown
### Try to break it

DPC-001 v0.2 has been tested only by its builders: one person and two AI systems. That is not independent
validation. If you can find a study design it labels wrongly under its own spec, a crash, or a label that
changes when only the wording changes, please report it on [issue #N](link). <!-- #N and link are filled in only after the issue is actually created, with Chad's separate authorization --> The issue has a one-command
reproduction and a submission format.

**Known and disclosed:** the checker trusts the facts it is given. A made-up evidence reference or a false
attestation is accepted (spec §4). That is not a new finding.

Confirmed breaks are kept as failures of v0.2 and credited to whoever found them.
```

---

## Open points for review (ChatGPT, then Chad)

1. **Where to post.** In `veritas-origin` as a normal issue? The repository is public.
2. **Scope.** Should the challenge also cover the pre-seal gate (`preseal_gate.py`)? This draft keeps it to the checker.
3. **Credit wording.** Is "credited by name, or as you prefer" enough?
4. **Audit caveats.** ChatGPT's audit (note 044) is reflected only as "not independent validation". Should note 044's limits on the property tests appear in the issue too?
5. **Ordering.** Chad has said PR #25 should not be merged without his authorization. Until then, the issue's links point at commit `bc43adf`, not at `main`. That works, but readers will see an unmerged branch.
