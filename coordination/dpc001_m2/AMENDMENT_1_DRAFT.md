# DPC-001-M2 — Amendment 1 (proposed before implementation)

**Status: DRAFT_FOR_OWNER_REVIEW / STATIC_DESIGN_FINDINGS / NOT_IMPLEMENTED / NOT_RUN.**
Authored by ChatGPT (GPT-6) during the 2026-10-10 Veritas-Origin continuation. The original preregistration at commit `3c4abb07f2a6b9f7377f1bc115abe3ebbf060912` is preserved unchanged. This document proposes prospective corrections; it is **not** an after-the-fact reinterpretation of a test result.

## Evidence inspected (read-only static review)

1. `coordination/dpc001_v02/visible_cases_v02.json` at frozen `bc43adf3` has 55 cases, of which **A03** sets `facts.bound.max_abs_contrast: NaN` and **A04** sets `facts.bound.threshold: Infinity` (Python permissive JSON literals, not standard JSON).
2. Pinned `preseal_gate.py` at `45ccccc` uses `json.load(parse_constant=bad_const)`: it rejects `NaN` and `Infinity`, reports `COULD NOT CHECK`, and exits **2**. If a generator attempts strict JSON serialization instead, it must reject these source values before writing. Either way, the registered 55-case base is incompatible with C1's required gate PASS.
3. Registered E1 **appends** a copied case under a new ID, yielding 56 entries while the gate expects 55. The G1 count check can reject E1 even if G3 duplicate detection is inoperative, confounding the alleged G3 interception.
4. The pinned gate's G4 has only four intent-precondition checks, so E11 must be chosen without accidentally invoking one of those checks. This is a clarification of attribution, not evidence of another observed failure.

**No M2 plant, C1 control, gate execution, mutant execution, or checker execution has been performed for these findings.**

## Proposed prospective corrections

**A1 — valid baseline domain.** Retain the frozen 55-case source unmodified, but construct baseline `B_valid` from all cases **except A03 and A04**. Record both exclusions and source IDs in a manifest; no silent normalization or replacement. `B_valid` thus contains 53 cases, with the gate called using `--count 53`. C1 requires `PRESEAL_GATE PASS` (exit 0) on this exact set. If C1 fails for any additional reason, record the failure and stop **INCONCLUSIVE**, without choosing further exclusions or changing the base. Keep seed 20261010, 20 plants per class and 220 total planned sets. The original 55-case proposal remains readable in the unedited registration.

**A2 — isolate E1's G3 mechanism.** E1 must preserve exactly 53 cases, 53 unique ordered case IDs, and 53 matching oracle entries. Choose distinct case IDs `target` and `source` whose original expected primary labels differ. In the planted copy **replace only `target.contract`** with a deep copy of `source.contract`, retaining `target.contract.study_id` (and `target.case_id`); retain both oracle entries and their different primary labels. The source and target contracts are then identical *apart from study_id*, exactly the predicate G3 examines, without changing the count or ID order. A credited E1 catch must include a **G3 FAIL** naming the pair; G1-only rejection is contaminated and must not count as a G3 detection.

**A3 — targeted-check attribution.** Report all failure lines and codes. A plant counts as caught by its registered mechanism only if the relevant G3/G4/G2/G1/G5 line is present and explicitly matches the planted case or predicate. A nonzero exit from an unrelated check alone is a **confounded result**, not a successful catch; report it separately, with no retuning after results. C3's G4-removed mutant remains a temporary, digest-recorded copy and must be checked for incidental catches.

**A4 — eligibility / E11.** For E2–E5 select 20 distinct cases whose unmodified contracts satisfy each claimed positive precondition (valid schema, nonempty study_id, valid review phase, `facts` object, respectively); record candidate pool, deterministic selection method, and chosen case IDs before the first run. For E11 choose a known, spec-valid reason code that is incorrect for the target and is not one of G4's four special codes (`SCHEMA_INVALID`, `STUDY_ID_MISSING`, `REVIEW_PHASE_INVALID`, `FACTS_MISSING`). Record the provenance of the chosen reason-code vocabulary without running the checker as an oracle. Verify every plant's single intended edit, including unchanged IDs and counts except the explicitly registered E7–E9 modifications.

## What remains unchanged

- **Instrument:** original gate at `45ccccc`, SHA-256 `c407364c990ef819e6ca8937d4395d3f4bc6d36bef8ac25210776d02bf24cdd6` (verify before a run).
- **Classes:** E1–E11, predictions caught E1–E9 and missed E10–E11, and per-class acceptance thresholds ≥19/20 and ≤1/20, respectively.
- **Controls:** C1–C4 with A1/A2 attribution clarified.
- **Evidence:** 220 per-set outcomes, hashes, seed, provenance, negative results and exact gate output; no withheld or sealed inputs used.
- **Limits:** simulated/planted author-designed error classes do not establish a real-world author error rate; no upgrade to independent validation.

## Execution interlock

Implementation and execution remain **separate steps**. This amendment is a proposal prepared *before either step*. Before implementation, review whether A1–A4 accurately preserve the intended hypothesis, then explicitly mark the amended plan accepted or rejected. Before the one registered run, pin the amended plan and generated instrument digests, check C1 and C2, and resolve failures as recorded outcomes rather than improvising more edits. No experiment is authorized by this draft alone.
