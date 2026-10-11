# DPC-001-M2: how reliably does the pre-seal gate catch planted test-author errors?

**Status: REGISTERED, NOT IMPLEMENTED, NOT RUN.** This file is committed alone. No generator, runner or
planted set exists. Registered 2026-10-10 by Claude (Opus 5.5) at Chad Holland's direction. Implementation and
execution each need his separate authorization. He has not reviewed it line by line.

## Why

Finding DPC-001-M1 (`FINDING_M1.md`, `5d01901`) records one observation: the pre-seal gate caught one test-author
error (run 2 draft, T03) before sealing. One catch of one error class is not a rate. M2 measures the gate's catch
rate per error class on planted errors, including the classes it is *not* designed to catch, so the result can
show its limits as well as its strengths.

## Instrument (pinned)

`coordination/dpc001_v02/preseal_gate.py` at `45ccccc`, sha256
`c407364c990ef819e6ca8937d4395d3f4bc6d36bef8ac25210776d02bf24cdd6`. Its digest is checked at run time, and a
mismatch makes the run INCONCLUSIVE. The gate never runs the checker. Nor will M2.

## Material: visible cases only

- **Base set B:** the 55 visible cases in `visible_cases_v02.json` (sha256 `4b7cd3ab…`), converted to the gate's
  input format:
  - each case's contract is `base_contract` merged with its overrides, using `run_acceptance.py`'s merge rule;
  - each expected primary is its `expect`;
  - its required reason codes are its `reasons_any`;
  - the gate is called with `--count 55`.
- **No withheld or sealed material is used.** Run 2's sealed set stays sealed, and run 1's unsealed set is not
  used either, to keep the base independent of the error M1 came from.

## Error classes (one planted error per copy)

| Class | Planted error | Gate check it targets | Prediction |
|---|---|---|---|
| E1 | Copy one case under a new id, with a different expected label | G3 | **caught** |
| E2 | Require `SCHEMA_INVALID` on a case whose contract has the valid schema | G4 | **caught** |
| E3 | Require `STUDY_ID_MISSING` on a case with a non-blank `study_id` | G4 | **caught** |
| E4 | Require `REVIEW_PHASE_INVALID` on a case with a valid phase | G4 | **caught** |
| E5 | Require `FACTS_MISSING` on a case with a facts object | G4 | **caught** |
| E6 | Expected label outside the six spec labels (e.g. `READY`) | G2 | **caught** |
| E7 | Oracle id order or ids differ from the cases | G1 | **caught** |
| E8 | One case removed from both files (count 54, gate told 55) | G1 | **caught** |
| E9 | A malformed entry (non-object, or missing `case_id`) | G5 | **caught** (FAIL, no traceback) |
| E10 | **Semantically wrong label:** expected primary changed to another valid label, with no structural trace | none (declared out of scope) | **missed** |
| E11 | **Wrong but producible reason code:** a code the contract could produce, but the wrong one | none | **missed** |

- **Plants per class:** 20, applied to 20 different base cases drawn with a fixed seed (20261010). E7, E8 and E9
  use 20 different positions.
- **Total:** 220 planted sets, each scored by one gate call.

## Measures and acceptance criteria (per class; never pooled)

- **Catch rate per class:** the fraction of the 20 plants for which the gate exits 1, with a FAIL line naming the
  planted case or check.
- A class counts as **reliably caught** at **≥ 19 of 20** (95%), and as **missed** at **≤ 1 of 20**. Anything
  in between is reported as **partial**, with each miss listed.
- **M1's general claim is supported only if every class E1–E9 is reliably caught.** That claim is "the gate
  intercepts structural test-author errors before sealing". Any E1–E9 class below 19 of 20 refutes it for that
  class. The refutation is kept.
- **E10 and E11 are predicted to be missed.** If either is caught at ≥ 2 of 20, that is a surprise to explain,
  not a success to claim.

## Anti-vacuity controls

- **C1:** the unplanted base B must give `PRESEAL_GATE PASS` (exit 0). If it does not, the run is INCONCLUSIVE and
  the base problem is reported.
- **C2:** the gate's own self-test must pass (9/9) at run start.
- **C3:** a gate mutant with check G4 removed, in a temporary copy only, must miss E2–E5 (each ≤ 1 of 20). That
  shows the measured catches come from G4 and not from something incidental.
- **C4:** every planted set is checked by a separate assertion to differ from B in exactly the planted way, so
  an unapplied plant cannot pass as a "miss".

## Evidence

- `results/dpc001_m2/` will hold:
  - the generator's and runner's sha256;
  - the seed;
  - for each of the 220 sets: its digest, the gate's exit code and its FAIL lines;
  - the controls;
  - `SHA256SUMS`.
- Results are written failures first, with numbers pasted from the log.

## What this cannot establish

- **The plants are Claude's construction.** Claude also wrote the gate, so these are errors its author thought of.
  Real test authors' error mix and rate are unknown, so this is detection per class, not a rate in practice.
- **55 visible cases, one schema version.** Other test-set shapes may behave differently.
- **E10 and E11 mark the gate's design boundary.** Catching wrong-but-well-formed expectations needs a second
  author or the checker, and the gate deliberately uses neither.
- **Not independent. NOT VALIDATED.**
