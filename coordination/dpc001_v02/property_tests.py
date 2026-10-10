"""Property-based stress tests for the frozen DPC-001 v0.2 checker. No answer key: each property
comes from the spec (SPEC_V02_DRAFT.md §1–§3, D1–D6), and is checked on thousands of random contracts.

Written by Claude (Opus 5.5), 2026-10-09, at Chad Holland's direction. Claude also wrote the checker, so
these are development tests, NOT independent evidence; their value is that a broken property is
unambiguous (no expected label chosen by anyone).

PREDICTIONS, registered in this commit before the first run:
  On the frozen checker (sha256 f2746a43…), with seed 20261009 and N = 10000 random contracts,
  every property P1–P8 holds (0 violations).
  On each of the four mutant checkers (M1–M4 below), at least one property is violated.
  If the frozen checker violates any property, that is a finding against v0.2 (a fix would be v0.3).

PROPERTIES
  P1 totality      any input -> exactly one of the six labels, a list of reason codes, no exception
  P2 determinism   same input twice -> same output; the input object is not modified
  P3 key order     shuffling the order of keys in every mapping -> same label
  P4 prose         rewriting every prose field (presence kept) -> same label
  P5 invalid wins  setting any one invalidating fact (spec §3 step 1) -> CONTRACT_INVALID
  P6 no defect helps  applying any one readiness defect (spec §3 step 5) -> never READY_FOR_COMPARISON
  P7 READY needs all  label READY -> every readiness condition of spec §3 step 5 holds
  P8 ND needs D4   label NONDISCRIMINATING -> ATTESTED, artifact present, admissible bound, threshold > max

Usage: python3 -I property_tests.py [N]      (run from this directory)
"""
import copy, importlib.util, json, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SEED, N = 20261009, int(sys.argv[1]) if len(sys.argv) > 1 else 10000
LABELS = {"CONTRACT_INVALID", "STRUCTURAL_TEST", "NONDISCRIMINATING_ENDPOINT", "DEMONSTRATION",
          "INSUFFICIENT_INFORMATION", "READY_FOR_COMPARISON"}
PROSE = {"source": ["repository", "revision_sha", "protocol_path", "protocol_sha256", "fixture_or_generator_revision", "evidence_provenance"],
         "claim": ["hypothesis", "intended_contribution", "primary_endpoint", "unit_of_analysis", "denominator", "direction", "success_threshold", "minimum_meaningful_effect"],
         "design": ["task_distribution", "policy_inputs_allowed", "protected_oracle", "calibration_data", "evaluation_data", "resources", "stop_rule"],
         "comparators": ["primary_strong_baseline", "baseline_selection_reason", "omitted_competitors", "trivial_floor_controls"],
         "feasibility": ["contrast_bound", "forecast_method", "forecast_input_provenance", "planned_precision", "assumptions_and_failure_modes"],
         "threat_scope": ["tested_mechanism_or_attack", "positive_control", "negative_control"]}


def load(path, patch=None):
    src = open(path, encoding="utf-8").read()
    if patch:
        old, new = patch
        assert src.count(old) == 1, f"mutant patch not found once: {old[:40]}"
        src = src.replace(old, new)
    ns = {"__name__": "dpc_checker"}
    exec(compile(src, path, "exec"), ns)
    return ns["classify"]


def num(rng):
    return rng.choice(["UNKNOWN", "NOT_APPLICABLE", round(rng.uniform(0.01, 40), 2), rng.randint(1, 50)])


def random_contract(rng):
    c = {"schema": "dpc-study-v0.2", "study_id": f"P-{rng.randrange(10**6)}",
         "review_phase": rng.choice(["PROSPECTIVE", "RETROSPECTIVE_DIAGNOSTIC"])}
    for sec, keys in PROSE.items():
        c[sec] = {k: f"{sec}.{k} text {rng.randrange(1000)}" for k in keys}
    c["claim"]["claim_kind"] = rng.choice(["STRUCTURAL", "DESCRIPTIVE_RATE", "COMPARATIVE_EFFECT"])
    structural = c["claim"]["claim_kind"] == "STRUCTURAL"
    c["facts"] = {
        "registration": {"relabels_registered_outcome": rng.random() < 0.1, "outcome_informed_design_choice": rng.random() < 0.1},
        "construct": {"structural_scope": rng.choice(["ENUMERATED", "ENUMERATED", "BROAD"]) if structural else rng.choice(["NOT_STRUCTURAL"] * 9 + ["ENUMERATED"]),
                      "structural_includes_rate_claim": rng.random() < 0.1,
                      "rate_population": rng.choice(["NOT_A_RATE_CLAIM", "SAMPLED_FROM_TARGET", "CONSTRUCTED_NOT_SAMPLED"]),
                      "rate_generalized_beyond_sample": rng.random() < 0.3},
        "oracle": {"policy_inputs_include_eval_labels": rng.random() < 0.1,
                   "label_oracle_role": rng.choice(["NONE"] * 6 + ["OPTIMISTIC_BOUND_ONLY", "USED_AS_HEADROOM_EVIDENCE", "CLAIMED_ACHIEVABLE"])},
        "bound": {"kind": rng.choice(["ANALYTIC", "ANALYTIC", "INDEPENDENT_CALIBRATION", "OBSERVED_PILOT", "OBSERVED_OUTCOME", "NONE"]),
                  "max_abs_contrast": num(rng), "threshold": num(rng), "units": "units"},
        "comparator": {"strength": rng.choice(["STRONG_PRIOR_ART", "STRONG_PRIOR_ART", "TRIVIAL_FLOOR_ONLY", "UNRESOLVED", "NOT_APPLICABLE_STRUCTURAL"]),
                       "contribution": rng.choice(["NOVEL_ADVANTAGE", "REPLICATION", "CORRECTNESS", "DEMONSTRATION"])},
        "forecast": {"status": rng.choice(["PREDECLARED_FORECAST", "PREDECLARED_FORECAST", "ANALYTICALLY_PREDICTABLE", "UNCERTAIN", "UNAVAILABLE", "NOT_APPLICABLE"])},
        "precision": {"status": rng.choice(["ESTIMATED", "ESTIMATED", "UNKNOWN", "NOT_APPLICABLE_STRUCTURAL"]), "mde": num(rng), "min_effect": num(rng),
                      "calibration_disjoint": rng.choice(["YES", "YES", "NO", "UNKNOWN", "NOT_APPLICABLE"]),
                      "independent_units": rng.choice([rng.randint(1, 500), "UNKNOWN", "NOT_APPLICABLE"]), "units": "units"},
        "controls": {"positive": rng.random() < 0.9, "negative": rng.random() < 0.9},
        "attestation": {"status": rng.choice(["ATTESTED", "ATTESTED", "UNATTESTED", "CONTESTED"]),
                        "bound_artifact": rng.choice(["proofs/bound.md@abc123", "proofs/bound.md@abc123", "NONE"])},
    }
    return c


def ready_contract(rng):
    """A contract that satisfies every readiness condition of spec §3 (used for P6/P7 seeds)."""
    c = random_contract(rng)
    c["review_phase"] = "PROSPECTIVE"; c["claim"]["claim_kind"] = "COMPARATIVE_EFFECT"
    f = c["facts"]
    f["registration"] = {"relabels_registered_outcome": False, "outcome_informed_design_choice": False}
    f["construct"].update(structural_scope="NOT_STRUCTURAL", structural_includes_rate_claim=False)
    f["oracle"] = {"policy_inputs_include_eval_labels": False, "label_oracle_role": rng.choice(["NONE", "OPTIMISTIC_BOUND_ONLY"])}
    mx = round(rng.uniform(1, 40), 2)
    f["bound"].update(kind=rng.choice(["ANALYTIC", "INDEPENDENT_CALIBRATION"]), max_abs_contrast=mx, threshold=round(rng.uniform(0.01, mx), 2))
    f["comparator"] = {"strength": "STRONG_PRIOR_ART", "contribution": rng.choice(["NOVEL_ADVANTAGE", "REPLICATION", "CORRECTNESS"])}
    f["forecast"]["status"] = "PREDECLARED_FORECAST"
    me = round(rng.uniform(0.5, 10), 2)
    f["precision"].update(status="ESTIMATED", min_effect=me, mde=round(rng.uniform(0.01, me), 2), calibration_disjoint="YES", independent_units=rng.randint(2, 500))
    f["attestation"] = {"status": "ATTESTED", "bound_artifact": "proofs/bound.md@abc123"}
    return c


def setf(path, value):
    def apply(c):
        d = c
        *head, last = path
        for k in head:
            d = d[k]
        d[last] = value
    return apply


INVALIDATING = {  # spec §3 step 1 (each applied alone must give CONTRACT_INVALID)
    "relabel": [setf(("facts", "registration", "relabels_registered_outcome"), True)],
    "outcome-informed (prospective)": [setf(("review_phase",), "PROSPECTIVE"), setf(("facts", "registration", "outcome_informed_design_choice"), True)],
    "observed-outcome bound (prospective)": [setf(("review_phase",), "PROSPECTIVE"), setf(("facts", "bound", "kind"), "OBSERVED_OUTCOME")],
    "eval labels as policy input": [setf(("facts", "oracle", "policy_inputs_include_eval_labels"), True)],
    "oracle claimed achievable": [setf(("facts", "oracle", "label_oracle_role"), "CLAIMED_ACHIEVABLE")],
    "structural + rate claim": [setf(("claim", "claim_kind"), "STRUCTURAL"), setf(("facts", "construct", "structural_includes_rate_claim"), True)],
    "structural + broad scope": [setf(("claim", "claim_kind"), "STRUCTURAL"), setf(("facts", "construct", "structural_scope"), "BROAD")],
    "structural + no positive control": [setf(("claim", "claim_kind"), "STRUCTURAL"), setf(("facts", "controls", "positive"), False)],
    "non-structural + structural scope": [setf(("claim", "claim_kind"), "COMPARATIVE_EFFECT"), setf(("facts", "construct", "structural_scope"), "ENUMERATED")],
    "constructed rate generalized": [setf(("claim", "claim_kind"), "DESCRIPTIVE_RATE"), setf(("facts", "construct", "structural_scope"), "NOT_STRUCTURAL"),
                                     setf(("facts", "construct", "structural_includes_rate_claim"), False),
                                     setf(("facts", "construct", "rate_population"), "CONSTRUCTED_NOT_SAMPLED"), setf(("facts", "construct", "rate_generalized_beyond_sample"), True)],
    "wrong schema": [setf(("schema",), "dpc-study-v0.1")],
    "facts block missing": [lambda c: c.pop("facts")],
    "unknown facts key": [setf(("facts", "extra"), True)],
    "NaN bound": [setf(("facts", "bound", "max_abs_contrast"), float("nan"))],
}
DEFECTS = {  # spec §3 step 5: each must block READY
    "unattested": setf(("facts", "attestation", "status"), "UNATTESTED"),
    "contested": setf(("facts", "attestation", "status"), "CONTESTED"),
    "no bound artifact": setf(("facts", "attestation", "bound_artifact"), "NONE"),
    "oracle as headroom": setf(("facts", "oracle", "label_oracle_role"), "USED_AS_HEADROOM_EVIDENCE"),
    "retrospective": setf(("review_phase",), "RETROSPECTIVE_DIAGNOSTIC"),
    "descriptive claim": setf(("claim", "claim_kind"), "DESCRIPTIVE_RATE"),
    "pilot bound": setf(("facts", "bound", "kind"), "OBSERVED_PILOT"),
    "no bound": setf(("facts", "bound", "kind"), "NONE"),
    "baseline unresolved": setf(("facts", "comparator", "strength"), "UNRESOLVED"),
    "trivial baseline": setf(("facts", "comparator", "strength"), "TRIVIAL_FLOOR_ONLY"),
    "forecast uncertain": setf(("facts", "forecast", "status"), "UNCERTAIN"),
    "forecast unavailable": setf(("facts", "forecast", "status"), "UNAVAILABLE"),
    "precision unknown": setf(("facts", "precision", "status"), "UNKNOWN"),
    "calibration not disjoint": setf(("facts", "precision", "calibration_disjoint"), "NO"),
    "one unit": setf(("facts", "precision", "independent_units"), 1),
    "mde above effect": lambda c: c["facts"]["precision"].update(mde=9.0, min_effect=1.0),
    "mde unknown": setf(("facts", "precision", "mde"), "UNKNOWN"),
}


def ready_conditions(c):
    f = c["facts"]; p = f["precision"]; b = f["bound"]
    isnum = lambda v: isinstance(v, (int, float)) and not isinstance(v, bool)
    return all([c["review_phase"] == "PROSPECTIVE", c["claim"]["claim_kind"] == "COMPARATIVE_EFFECT",
                f["attestation"]["status"] == "ATTESTED", f["attestation"]["bound_artifact"].strip().upper() != "NONE",
                f["oracle"]["label_oracle_role"] in ("NONE", "OPTIMISTIC_BOUND_ONLY"), not f["oracle"]["policy_inputs_include_eval_labels"],
                b["kind"] in ("ANALYTIC", "INDEPENDENT_CALIBRATION"), f["comparator"]["strength"] == "STRONG_PRIOR_ART",
                f["forecast"]["status"] == "PREDECLARED_FORECAST", p["status"] == "ESTIMATED", p["calibration_disjoint"] == "YES",
                isinstance(p["independent_units"], int) and p["independent_units"] >= 2,
                isnum(p["mde"]) and isnum(p["min_effect"]) and p["mde"] <= p["min_effect"]])


def shuffled(o, rng):
    if isinstance(o, dict):
        items = list(o.items()); rng.shuffle(items)
        return {k: shuffled(v, rng) for k, v in items}
    return o


def check(classify, n, seed):
    rng = random.Random(seed)
    viol = {f"P{i}": 0 for i in range(1, 9)}
    first = {}

    def bad(p, why):
        viol[p] += 1
        first.setdefault(p, why)

    def safe(c):
        try:
            r = classify(c)
            if not (isinstance(r, dict) and r.get("primary") in LABELS and isinstance(r.get("reason_codes"), list)):
                return None, f"bad shape {str(r)[:80]}"
            return r, None
        except Exception as e:
            return None, f"{type(e).__name__}: {e}"

    for i in range(n):
        c = ready_contract(rng) if i % 4 == 0 else random_contract(rng)
        snap = json.dumps(c, sort_keys=True)
        r, err = safe(c)
        if err:
            bad("P1", err); continue
        lab = r["primary"]
        r2, _ = safe(c)
        if json.dumps(c, sort_keys=True) != snap or r2 is None or r2["primary"] != lab:
            bad("P2", "nondeterministic or input mutated")
        r3, _ = safe(shuffled(copy.deepcopy(c), rng))
        if r3 is None or r3["primary"] != lab:
            bad("P3", f"key order changed {lab} -> {r3 and r3['primary']}")
        pc = copy.deepcopy(c)
        for sec, keys in PROSE.items():
            for k in keys:
                pc[sec][k] = f"rewritten {rng.randrange(10**6)}"
        r4, _ = safe(pc)
        if r4 is None or r4["primary"] != lab:
            bad("P4", f"prose changed {lab} -> {r4 and r4['primary']}")
        name = rng.choice(sorted(INVALIDATING)); x = copy.deepcopy(c)
        for f in INVALIDATING[name]:
            f(x)
        r5, err5 = safe(x)
        if err5 or r5["primary"] != "CONTRACT_INVALID":
            bad("P5", f"'{name}' gave {err5 or r5['primary']}")
        dname = rng.choice(sorted(DEFECTS)); y = copy.deepcopy(c); DEFECTS[dname](y)
        r6, err6 = safe(y)
        if err6 or r6["primary"] == "READY_FOR_COMPARISON":
            bad("P6", f"defect '{dname}' gave {err6 or r6['primary']}")
        if lab == "READY_FOR_COMPARISON" and not ready_conditions(c):
            bad("P7", "READY without every readiness condition")
        if lab == "NONDISCRIMINATING_ENDPOINT":
            b, a = c["facts"]["bound"], c["facts"]["attestation"]
            ok = (a["status"] == "ATTESTED" and a["bound_artifact"].strip().upper() != "NONE"
                  and (b["kind"] in ("ANALYTIC", "INDEPENDENT_CALIBRATION") or (b["kind"] == "OBSERVED_OUTCOME" and c["review_phase"] != "PROSPECTIVE"))
                  and isinstance(b["threshold"], (int, float)) and isinstance(b["max_abs_contrast"], (int, float)) and b["threshold"] > b["max_abs_contrast"])
            if not ok:
                bad("P8", "ND without the D4 conditions")
    return viol, first


MUTANTS = {  # deliberately broken checkers; each must break at least one property
    "M1 READY ignores attestation": ('    if att["status"] != "ATTESTED":\n        missing.append("FACTS_UNATTESTED")\n', ""),
    "M2 eval-label check removed": ('ora["policy_inputs_include_eval_labels"] or ', ""),
    "M3 ND skips D4": ('if corroborated and att["status"] == "ATTESTED":', "if True:"),
    "M4 crashes on unknown units": ('    if missing:\n        gates.update(G5="UNKNOWN")', '    if missing:\n        assert pr["independent_units"] != "UNKNOWN"\n        gates.update(G5="UNKNOWN")'),
}


def main():
    path = os.path.join(HERE, "checker.py")
    viol, first = check(load(path), N, SEED)
    total = sum(viol.values())
    print(f"== frozen checker, N={N}, seed={SEED}")
    for p, v in viol.items():
        print(f"{'ok ' if v == 0 else 'BAD'}  {p}  violations {v}" + (f"   first: {first[p]}" if v else ""))
    print(f"PROPERTIES  {'ALL HOLD' if total == 0 else f'{total} VIOLATIONS'}")
    print("\n== anti-vacuity: mutant checkers (each must break a property)")
    caught = 0
    for name, patch in MUTANTS.items():
        mv, _ = check(load(path, patch), min(N, 4000), SEED)
        hit = [p for p, v in mv.items() if v]
        caught += bool(hit)
        print(f"{'caught' if hit else 'MISSED'}  {name}  -> {', '.join(hit) or 'no property broken'}")
    print(f"MUTANTS  {caught} of {len(MUTANTS)} caught")
    return 0 if total == 0 and caught == len(MUTANTS) else 1


if __name__ == "__main__":
    sys.exit(main())
