# DPC-001 test plan (Phase B): written by Claude from the frozen spec

- **Spec under test:** `coordination/specs/DPC001_DISCRIMINATION_PRECHECK_DRAFT.md`, commit `d05501013c7b2d0c602893e44d157620b55f12ff`, SHA-256 `c02a1daaaa9858ce0c3cef3c85f0ed995c0e4b966f458c977f8b6ef87c259cf9`. Frozen by Chad Holland on 2026-10-09 (PR #16 comment 6084151225), before these tests were written.
- **Author:** Claude (Opus 5.5), self-declared. Chad directed the work and has not reviewed these cases line by line. No checker implementation existed or was read when they were written.
- **Scope:** tests and harness only. Building a checker and running the acceptance run each need a further owner decision (spec §7 step 6).

## Contents
| File | What |
|---|---|
| `visible_cases.json` | 20 visible cases (V01–V20): one valid base contract plus per-case overrides, the expected primary label, the spec section that decides it, and required reason codes where the spec names one |
| `WITHHELD_MANIFEST.md` | SHA-256 commitments for 6 withheld cases (H01–H06); contents held by Chad |
| `run_acceptance.py` | harness: merges each case, calls `classify(contract)`, compares, prints a confusion matrix; contains no classification logic |
| `mutants_out.txt` | the suite rejecting four trivial checkers (output below) |

## Coverage against spec §6
| Spec requirement | Cases |
|---|---|
| Nontrivial positive, strong rival, uncertain sign must be READY (no always-block) | V15, V16 (replication not auto-rejected), H05 (different domain) |
| Structural good/bad pair; mutations removing the good control or broadening scope | V04, V05, V11; V06 (positive control removed), V07 (scope broadened), H03 |
| Impossible margin under an admissible bound; a saturated small pilot is not proof | V17; V18 |
| Known result or weak comparator gives DEMONSTRATION | V03, H01 |
| Label-aware hindsight oracle repackaged as feasible | V08 (INSUFFICIENT + `ORACLE_LEAKAGE_TO_HEADROOM_ARGUMENT`), V09 (misrepresented access gives CONTRACT_INVALID) |
| Missing fields fail; honest unknowns stay INSUFFICIENT | V13; V14, H06 |
| Retrospective relabelling of a registered outcome fails | V20 |
| Historical fixtures in spec §5 | V01, V02 (EXP-003 both phases), V03/V04 (EXP-002), V05 (RK-1), V08 (ITC H2), V10/V11 (EPV), V12 (ASP) |
| Mixed structural plus rate claim (§8 Q1: separate IDs) | V19 |
| Leakage and post-hoc comparator exclusion | H02, H04 |

## Anti-vacuity of the suite itself (run, not a checker result)
```
VERDICT  2 of 20 cases as expected (mutant always_ready)
exit 1
VERDICT  4 of 20 cases as expected (mutant always_insufficient)
exit 1
VERDICT  7 of 20 cases as expected (mutant always_invalid)
exit 1
VERDICT  2 of 20 cases as expected (mutant always_structural)
exit 1
```
No single constant label passes. The best trivial score is 7/20 (always CONTRACT_INVALID), because 7 of 20 visible cases expect it. Visible label counts: CONTRACT_INVALID 7, INSUFFICIENT_INFORMATION 5, STRUCTURAL_TEST 3, NONDISCRIMINATING_ENDPOINT 2, READY_FOR_COMPARISON 2, DEMONSTRATION 1.

## Where the spec doesn't decide, and I chose (open to ChatGPT's challenge)
1. **V04:** a correctness check of a known algorithm is `STRUCTURAL_TEST`, not `DEMONSTRATION`. This follows spec §8 Q2's proposed reading.
2. **V19:** a mixed structural-plus-rate contract is `CONTRACT_INVALID`, following spec §8 Q1's proposed answer ("separate study IDs").
3. **H04 (withheld; this sentence names the case without its contents):** one withheld case turns on whether a post-hoc decision about comparators is "irreversible leakage" (G0) or an honest gap. I chose the stricter label.
4. **V10 vs V11:** the same EPV fixture gets different labels depending only on the claim made. This is intended (spec §5 row 5).
5. **Reason codes** are required only where the spec itself names one (`ORACLE_LEAKAGE_TO_HEADROOM_ARGUMENT`, `THREAT_COVERAGE_LIMITED`). Everything else is judged on the primary label, so the spec isn't extended through the tests.

If a case's expected label turns out to be wrong under the frozen spec, it gets a dated correction note, never a silent edit. A disputed label goes to `CONTESTED` after at most two rounds (spec §7).

## How to run it later (not authorised yet)
`python3 -I run_acceptance.py --checker path/to/checker.py:classify visible_cases.json withheld_cases.json`, once, with every result kept.
