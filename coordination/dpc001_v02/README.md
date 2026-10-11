# DPC-001 v0.2 draft: typed-facts checker

## Current research status — 2026-10-10

**FROZEN / NOT INDEPENDENTLY VALIDATED / PR #25 OPEN.** The original draft-language below is historical, not the current status. Owner approval of D1–D6 and freeze are recorded in [FREEZE_RECORD.md](FREEZE_RECORD.md): spec and checker frozen at `bc43adf3b51633dfb831ce420afe90ec3ac04ab7`. No code or frozen specification changes are authorized here.

- **Blind run 1:** FAIL 23/24. The [published run-1 evidence](blind_run_1/evidence/blind_run_v1.json) preserves T01's test-author oracle error. The retrospective pre-seal gate found that error; it was not in place when run 1 executed.
- **Blind run 2:** PASS 24/24 **owner-reported**, not independently reproducible from this PR; the sealed case set, oracle, runner and result are absent. See [blind_run_2/RECORD.md](blind_run_2/RECORD.md). The freeze record's original `BLIND_TEST_NOT_AUTHORIZED` describes freeze time; subsequent owner-authorized runs supersede it operationally.
- **Test limits:** 55/55 visible cases and 110/110 prose rewrites were Claude-reported. Prose invariance tests primary-label independence from wording, not correctness or truth. Property tests used 10,000 generated structured contracts, not arbitrary Python inputs; P2 checks label repeatability/input preservation rather than full output equality, P3/P4 primary-label equivalence, and P7/P8 embed shared spec assumptions. Four selected mutants show sensitivity, not mutation adequacy; the property script lacks its own frozen-file hash check. See [review note 044](https://github.com/holland202/veritas-origin/pull/25#issuecomment-6092639328).
- **ADV-001 correction:** **8/8 results as expected, not 7/8 rejected**: six CONTRACT_INVALID and two READY (control plus ADV-02). Claude mapped the attack ideas and tried an informal run before writing expectations: not blind or preregistered. The fake artifact reference in ADV-02 yields READY by declared facts, not authenticated provenance. See [correction note 046](https://github.com/holland202/veritas-origin/pull/25#issuecomment-6092686978).
- **Unclosed top-level schema:** extra root keys like `author`, `auditor`, and `status: VALIDATED` are ignored under the frozen v0.2 rules, which close only `facts`. This is not a frozen-spec violation but may mislead downstream readers; a closed root schema is a possible v0.3 owner decision. See [finding note 047](https://github.com/holland202/veritas-origin/pull/25#issuecomment-6092705020).
- **Epistemic boundary:** the checker does not verify declared fact truth, attestation authenticity, or referenced artifacts. Claude wrote the checker, visible cases and property tests; ChatGPT authored the blind cases after reading the code. No independent scientific validation is claimed. Preserve v0.1 negatives, run-1 FAIL and M1's single observed interception without generalizing a detection rate.

This documentation reconciliation authorizes **no** new test, publication, merge, or v0.3 implementation.

---

DRAFT, NOT FROZEN, NOT VALIDATED. Written by Claude (Opus 5.5), 2026-10-09, at Chad Holland's direction; not reviewed line by line. Read `SPEC_V02_DRAFT.md` first.

## Run outputs (pasted as printed, `python3 -I`, at this commit)

```
VERDICT  55 of 55 cases as expected (checker checker.py:classify)
VERDICT  3 of 55 cases as expected (mutant always_ready)
VERDICT  16 of 55 cases as expected (mutant always_insufficient)
VERDICT  25 of 55 cases as expected (mutant always_invalid)
VERDICT  2 of 55 cases as expected (mutant always_structural)
$ python3 -I prose_invariance.py checker.py:classify visible_cases_v02.json
VERDICT  110 of 110 rewrites kept the label

# anti-vacuity: the same invariance test on the PR #24 checker @943ebb4 (v0.1 cases)
VERDICT  19 of 40 rewrites kept the label
```

## Files

| File | What |
|---|---|
| `SPEC_V02_DRAFT.md` | amendment to the frozen v0.1 spec: typed `facts`, attestation, invariants, decision procedure, owner-decision table (§7) |
| `checker.py` | decides from `facts` only; prose is checked for presence, never read for meaning |
| `visible_cases_v02.json` | 20 v0.1 visible cases (prose and labels unchanged) with facts, 16 one-fact flips (F), 19 adversarial cases (A) |
| `build_cases_v02.py` | regenerates the cases file from v0.1 `visible_cases.json` (PR #20) |
| `prose_invariance.py` | rewrites every prose field; labels must not change. Shows only that prose is ignored, not that contracts are admissible |
| `run_acceptance.py` | unchanged copy of the PR #20 harness (sha256 `84a918c2…`) |

**Not independent:** Claude wrote this checker and all its visible cases, so the labels on V01–V20 match v0.1 by construction. The real test is a blind run on new withheld cases written by ChatGPT, held by Chad, after Chad decides D1–D6 and freezes the bytes.
