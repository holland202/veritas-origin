"""Pre-seal integrity gate for a DPC-001 blind test set. Runs BEFORE sealing; never runs the checker.

Written by Claude (Opus 5.5), 2026-10-09, after blind run 1's T01 oracle error (PR #25 note 029).
It checks the test set against itself and against the spec text only. It does not import the
checker and does not judge whether an expected label is right under the rules (that is the test
author's job). It catches the mechanical mistakes that let a broken case reach a blind run.

Input format (as in blind_run_1): cases.json = [{"case_id", "contract"}...],
oracle.json = [{"case_id", "primary", "required_reason_codes"?}...]

Checks
  G1 ids: same ordered, unique ids in both files; expected count
  G2 labels: every expected primary is one of the six spec labels
  G3 duplicates: two cases whose contracts are identical apart from study_id
     -> FAIL if their expected labels differ, WARN if the same (likely a mutation that was never applied)
  G4 declared-intent preconditions (spec-level, checker-free): a case whose oracle requires
     SCHEMA_INVALID must not carry the valid schema; STUDY_ID_MISSING needs a blank/absent study_id;
     REVIEW_PHASE_INVALID needs a phase outside the two spec values; FACTS_MISSING needs no facts object.
  G5 shape: every entry is an object with a string case_id (checked first; malformed input stops
     the gate with FAIL, never a traceback); every contract is a JSON object; no NaN/Infinity literals

Usage: python3 -I preseal_gate.py cases.json oracle.json [--count 24]
Exit 0 = PASS (no FAIL; WARNs printed), 1 = FAIL, 2 = could not read.
"""
import argparse, json, sys

LABELS = {"CONTRACT_INVALID", "STRUCTURAL_TEST", "NONDISCRIMINATING_ENDPOINT",
          "DEMONSTRATION", "INSUFFICIENT_INFORMATION", "READY_FOR_COMPARISON"}
VALID_SCHEMA = "dpc-study-v0.2"
PHASES = {"PROSPECTIVE", "RETROSPECTIVE_DIAGNOSTIC"}


def canon(o):
    return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def load(path):
    def bad_const(x):
        raise ValueError(f"non-finite literal {x}")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh, parse_constant=bad_const)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cases"); ap.add_argument("oracle"); ap.add_argument("--count", type=int, default=24)
    a = ap.parse_args()
    try:
        cases, oracle = load(a.cases), load(a.oracle)
    except (OSError, ValueError) as e:
        print(f"COULD NOT CHECK: {e}"); return 2
    fails, warns = [], []

    if not isinstance(cases, list) or not isinstance(oracle, list):
        print("FAIL  G5 both files must be JSON lists"); return 1
    # Structural pre-pass: every entry must be an object with a non-empty string case_id.
    # Malformed entries are reported as FAIL and stop the gate (no traceback, no partial checks).
    shape = [f"G5 {name} entry #{i}: {why}" for name, lst in (("cases", cases), ("oracle", oracle))
             for i, e in enumerate(lst)
             for why in (["not a JSON object"] if not isinstance(e, dict) else
                         [] if isinstance(e.get("case_id"), str) and e["case_id"].strip() else ["case_id missing or not a non-empty string"])]
    if shape:
        for f in shape:
            print("FAIL ", f)
        print(f"\nPRESEAL_GATE  FAIL  ({len(shape)} fail, 0 warn, {len(cases)} cases; stopped at shape check)")
        return 1
    cid = [c.get("case_id") if isinstance(c, dict) else None for c in cases]
    oid = [o.get("case_id") if isinstance(o, dict) else None for o in oracle]
    if cid != oid:
        fails.append("G1 case ids and oracle ids differ in content or order")
    if len(set(cid)) != len(cid) or None in cid:
        fails.append("G1 missing or duplicate case ids")
    if len(cid) != a.count:
        fails.append(f"G1 expected {a.count} cases, found {len(cid)}")

    con = {}
    for c in cases:
        if not isinstance(c, dict) or not isinstance(c.get("contract"), dict):
            fails.append(f"G5 {c.get('case_id') if isinstance(c, dict) else c!r}: contract is not an object")
        else:
            con[c["case_id"]] = c["contract"]
    exp = {o["case_id"]: o for o in oracle if isinstance(o, dict) and "case_id" in o}
    for k, o in exp.items():
        if o.get("primary") not in LABELS:
            fails.append(f"G2 {k}: expected label {o.get('primary')!r} is not a spec label")

    groups = {}
    for k, c in con.items():
        groups.setdefault(canon({x: v for x, v in c.items() if x != "study_id"}), []).append(k)
    for g in groups.values():
        if len(g) > 1:
            labels = {exp.get(k, {}).get("primary") for k in g}
            msg = f"G3 cases {g} have identical contracts apart from study_id"
            (fails if len(labels) > 1 else warns).append(msg + (f" but different expected labels {sorted(map(str, labels))}" if len(labels) > 1 else ""))

    for k, o in exp.items():
        c, need = con.get(k), set(o.get("required_reason_codes") or [])
        if c is None:
            continue
        if "SCHEMA_INVALID" in need and c.get("schema") == VALID_SCHEMA:
            fails.append(f"G4 {k}: oracle requires SCHEMA_INVALID but the contract carries the valid schema")
        if "STUDY_ID_MISSING" in need and isinstance(c.get("study_id"), str) and c["study_id"].strip():
            fails.append(f"G4 {k}: oracle requires STUDY_ID_MISSING but study_id is present")
        if "REVIEW_PHASE_INVALID" in need and c.get("review_phase") in PHASES:
            fails.append(f"G4 {k}: oracle requires REVIEW_PHASE_INVALID but the phase is valid")
        if "FACTS_MISSING" in need and isinstance(c.get("facts"), dict):
            fails.append(f"G4 {k}: oracle requires FACTS_MISSING but a facts object is present")

    for w in warns:
        print("WARN ", w)
    for f in fails:
        print("FAIL ", f)
    print(f"\nPRESEAL_GATE  {'FAIL' if fails else 'PASS'}  ({len(fails)} fail, {len(warns)} warn, {len(cid)} cases)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
