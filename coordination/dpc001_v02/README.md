# DPC-001 v0.2 draft: typed-facts checker

DRAFT, NOT FROZEN, NOT VALIDATED. Written by Claude (Opus 5.5), 2026-10-09, at Chad Holland's direction; not reviewed line by line. Read `SPEC_V02_DRAFT.md` first.

## Run outputs (pasted as printed, `python3 -I`, at this commit)

```
VERDICT  53 of 53 cases as expected (checker checker.py:classify)
VERDICT  3 of 53 cases as expected (mutant always_ready)
VERDICT  15 of 53 cases as expected (mutant always_insufficient)
VERDICT  25 of 53 cases as expected (mutant always_invalid)
VERDICT  2 of 53 cases as expected (mutant always_structural)
$ python3 -I prose_invariance.py checker.py:classify visible_cases_v02.json
VERDICT  106 of 106 rewrites kept the label

# anti-vacuity: the same invariance test on the PR #24 checker @943ebb4 (v0.1 cases)
VERDICT  19 of 40 rewrites kept the label
```

## Files

| File | What |
|---|---|
| `SPEC_V02_DRAFT.md` | amendment to the frozen v0.1 spec: typed `facts`, attestation, invariants, decision procedure, owner-decision table (§7) |
| `checker.py` | decides from `facts` only; prose is checked for presence, never read for meaning |
| `visible_cases_v02.json` | 20 v0.1 visible cases (prose and labels unchanged) with facts, 16 one-fact flips (F), 17 adversarial cases (A) |
| `build_cases_v02.py` | regenerates the cases file from v0.1 `visible_cases.json` (PR #20) |
| `prose_invariance.py` | rewrites every prose field; labels must not change. Shows only that prose is ignored, not that contracts are admissible |
| `run_acceptance.py` | unchanged copy of the PR #20 harness (sha256 `84a918c2…`) |

**Not independent:** Claude wrote this checker and all its visible cases, so the labels on V01–V20 match v0.1 by construction. The real test is a blind run on new withheld cases written by ChatGPT, held by Chad, after Chad decides D1–D6 and freezes the bytes.
