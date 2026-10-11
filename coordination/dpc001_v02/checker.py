"""DPC-001 v0.2 checker: decides from typed facts only, never from prose.

DRAFT proposal by Claude (Opus 5.5), 2026-10-09, at Chad Holland's direction. Not frozen,
not validated, not reviewed line by line. Spec: SPEC_V02_DRAFT.md in this directory.

Why: the v0.1 checker in PR #24 matched phrases in free text and flipped under
meaning-preserving rewording (visible 20/20; paraphrase round 2 1/8). Here every decision
reads the `facts` block (booleans, enums, numbers). The prose fields stay required (a human
reads them) but are only checked for presence, so rewording them cannot change a label.

What this does NOT do: check that the facts are true or match the prose. A contract can
declare false facts; that moves the hard judgement to whoever fills in and reviews `facts`.

classify(contract) -> {"primary": label, "reason_codes": [...], "gates": {...}}
Standard library only; no I/O.
"""
from __future__ import annotations

from numbers import Real
from typing import Any

SCHEMA = "dpc-study-v0.2"
LABELS = ("CONTRACT_INVALID", "STRUCTURAL_TEST", "NONDISCRIMINATING_ENDPOINT",
          "DEMONSTRATION", "INSUFFICIENT_INFORMATION", "READY_FOR_COMPARISON")

# Prose fields carried over from v0.1: required and non-empty, never interpreted.
PROSE = {
    "source": ("repository", "revision_sha", "protocol_path", "protocol_sha256",
               "fixture_or_generator_revision", "evidence_provenance"),
    "claim": ("hypothesis", "intended_contribution", "primary_endpoint", "unit_of_analysis",
              "denominator", "direction", "success_threshold", "minimum_meaningful_effect"),
    "design": ("task_distribution", "policy_inputs_allowed", "protected_oracle",
               "calibration_data", "evaluation_data", "resources", "stop_rule"),
    "comparators": ("primary_strong_baseline", "baseline_selection_reason",
                    "omitted_competitors", "trivial_floor_controls"),
    "feasibility": ("contrast_bound", "forecast_method", "forecast_input_provenance",
                    "planned_precision", "assumptions_and_failure_modes"),
    "threat_scope": ("tested_mechanism_or_attack", "positive_control", "negative_control"),
}
NA_STRUCTURAL = "NOT_APPLICABLE_STRUCTURAL"

B, N, I, S = "bool", "number|UNKNOWN|NOT_APPLICABLE", "count|UNKNOWN|NOT_APPLICABLE", "nonempty_string"
FACTS = {  # section -> field -> allowed type or enum values
    "registration": {"relabels_registered_outcome": B, "outcome_informed_design_choice": B},
    "construct": {
        "structural_scope": ("NOT_STRUCTURAL", "ENUMERATED", "BROAD"),
        "structural_includes_rate_claim": B,
        "rate_population": ("NOT_A_RATE_CLAIM", "SAMPLED_FROM_TARGET", "CONSTRUCTED_NOT_SAMPLED"),
        "rate_generalized_beyond_sample": B,
    },
    "oracle": {
        "policy_inputs_include_eval_labels": B,
        "label_oracle_role": ("NONE", "OPTIMISTIC_BOUND_ONLY", "USED_AS_HEADROOM_EVIDENCE", "CLAIMED_ACHIEVABLE"),
    },
    "bound": {
        "kind": ("ANALYTIC", "INDEPENDENT_CALIBRATION", "OBSERVED_PILOT", "OBSERVED_OUTCOME", "NONE"),
        "max_abs_contrast": N, "threshold": N, "units": S,
    },
    "comparator": {
        "strength": ("STRONG_PRIOR_ART", "TRIVIAL_FLOOR_ONLY", "UNRESOLVED", NA_STRUCTURAL),
        "contribution": ("NOVEL_ADVANTAGE", "REPLICATION", "CORRECTNESS", "DEMONSTRATION"),
    },
    "forecast": {"status": ("ANALYTICALLY_PREDICTABLE", "PREDECLARED_FORECAST", "UNCERTAIN",
                            "UNAVAILABLE", "NOT_APPLICABLE")},
    "precision": {
        "status": ("ESTIMATED", "UNKNOWN", NA_STRUCTURAL),
        "mde": N, "min_effect": N, "calibration_disjoint": ("YES", "NO", "UNKNOWN", "NOT_APPLICABLE"),
        "independent_units": I, "units": S,
    },
    "controls": {"positive": B, "negative": B},
    # Declared, not verified: who attested the facts, and the pinned artifact behind the bound.
    "attestation": {"status": ("ATTESTED", "UNATTESTED", "CONTESTED"), "bound_artifact": S},
}
# Range invariants on numeric facts (checked only when the value is a number).
# Convention: `threshold` is the positive magnitude of the required margin in the
# hypothesis's own direction; `max_abs_contrast` is the largest attainable |difference|.
RANGES = {("bound", "max_abs_contrast"): (0, True), ("bound", "threshold"): (0, False),
          ("precision", "mde"): (0, False), ("precision", "min_effect"): (0, False),
          ("precision", "independent_units"): (1, True)}  # (lower bound, inclusive?)


def _out(primary, reasons, gates):
    return {"primary": primary, "reason_codes": list(dict.fromkeys(reasons)), "gates": gates,
            "replay_status": "NOT_RUN",
            "limitations": ["Decides from declared typed facts; does not verify them against the prose or the world."]}


def _num(v):
    return isinstance(v, Real) and not isinstance(v, bool) and v == v and v not in (float("inf"), float("-inf"))


def _type_ok(v, t):
    if t == B:
        return isinstance(v, bool)
    if t == N:
        return v in ("UNKNOWN", "NOT_APPLICABLE") or _num(v)
    if t == I:
        return v in ("UNKNOWN", "NOT_APPLICABLE") or (isinstance(v, int) and not isinstance(v, bool))
    if t == S:
        return isinstance(v, str) and bool(v.strip())
    return isinstance(v, str) and v in t


def _validate(c) -> list[str]:
    if not isinstance(c, dict) or c.get("schema") != SCHEMA:
        return ["SCHEMA_INVALID"]
    bad = []
    if not isinstance(c.get("study_id"), str) or not c["study_id"].strip():
        bad.append("STUDY_ID_MISSING")
    if c.get("review_phase") not in ("PROSPECTIVE", "RETROSPECTIVE_DIAGNOSTIC"):
        bad.append("REVIEW_PHASE_INVALID")
    claim = c.get("claim")
    if not isinstance(claim, dict) or claim.get("claim_kind") not in ("STRUCTURAL", "DESCRIPTIVE_RATE", "COMPARATIVE_EFFECT"):
        bad.append("CLAIM_KIND_INVALID")
    structural = isinstance(claim, dict) and claim.get("claim_kind") == "STRUCTURAL"
    for sec, keys in PROSE.items():
        part = c.get(sec)
        if structural and sec == "comparators" and part == NA_STRUCTURAL:
            continue
        if not isinstance(part, dict):
            bad.append(f"SECTION_MISSING_{sec.upper()}")
            continue
        bad += [f"FIELD_MISSING_{sec.upper()}_{k.upper()}" for k in keys
                if not isinstance(part.get(k), str) or not part[k].strip()]
    facts = c.get("facts")
    if not isinstance(facts, dict):
        return bad + ["FACTS_MISSING"]
    # The facts block is strict: unknown sections or keys are rejected, not ignored.
    bad += [f"FACT_UNKNOWN_KEY_{str(k).upper()}" for k in facts if k not in FACTS]
    for sec, fields in FACTS.items():
        part = facts.get(sec)
        if not isinstance(part, dict):
            bad.append(f"FACTS_MISSING_{sec.upper()}")
            continue
        bad += [f"FACT_UNKNOWN_KEY_{sec.upper()}_{str(k).upper()}" for k in part if k not in fields]
        bad += [f"FACT_INVALID_{sec.upper()}_{k.upper()}" for k, t in fields.items()
                if k not in part or not _type_ok(part[k], t)]
    for (sec, k), (lo, inclusive) in RANGES.items():
        v = facts.get(sec, {}).get(k) if isinstance(facts.get(sec), dict) else None
        if _num(v) and (v < lo or (v == lo and not inclusive)):
            bad.append(f"FACT_OUT_OF_RANGE_{sec.upper()}_{k.upper()}")
    return bad


def classify(contract: dict[str, Any]) -> dict[str, Any]:
    """Advisory only. READY_FOR_COMPARISON never authorizes running anything."""
    bad = _validate(contract)
    gates = {g: "NOT_EVALUATED" for g in ("G0", "G1", "G2", "G3", "G4", "G5", "G6")}
    if bad:
        return _out("CONTRACT_INVALID", ["CONTRACT_MALFORMED"] + bad, gates)

    c, f = contract, contract["facts"]
    phase, kind = c["review_phase"], c["claim"]["claim_kind"]
    prospective = phase == "PROSPECTIVE"
    reg, con, ora, bnd = f["registration"], f["construct"], f["oracle"], f["bound"]
    cmp_, fc, pr, ctl = f["comparator"], f["forecast"], f["precision"], f["controls"]
    att = f["attestation"]
    corroborated = att["bound_artifact"].strip().upper() != "NONE"

    # (1) CONTRACT_INVALID: defective contract or misleading estimand.
    invalid = []
    if reg["relabels_registered_outcome"]:
        invalid.append("RETROSPECTIVE_OUTCOME_RELABELLING")                      # G0
    if prospective and (reg["outcome_informed_design_choice"] or bnd["kind"] == "OBSERVED_OUTCOME"):
        invalid.append("OUTCOME_LEAKAGE_INTO_PROSPECTIVE_DESIGN")                # G0
    if kind == "STRUCTURAL":
        if con["structural_includes_rate_claim"]:
            invalid.append("STRUCTURAL_RATE_CONFLATION")                         # G1
        if con["structural_scope"] != "ENUMERATED":
            invalid.append("THREAT_SCOPE_UNSUPPORTED")                           # G6
        if not (ctl["positive"] and ctl["negative"]):
            invalid.append("STRUCTURAL_CONTROL_MISSING")                         # G6
    elif con["structural_scope"] != "NOT_STRUCTURAL" or con["structural_includes_rate_claim"]:
        invalid.append("FACTS_INCONSISTENT_WITH_CLAIM_KIND")
    if kind == "DESCRIPTIVE_RATE" and con["rate_population"] == "CONSTRUCTED_NOT_SAMPLED" and con["rate_generalized_beyond_sample"]:
        invalid.append("SYNTHETIC_RATE_EXTRAPOLATION")                           # G1
    if ora["policy_inputs_include_eval_labels"] or ora["label_oracle_role"] == "CLAIMED_ACHIEVABLE":
        invalid.append("ORACLE_MISREPRESENTED_AS_FEASIBLE")                      # G2
    gates["G0"] = "FAIL" if any(r in invalid for r in ("RETROSPECTIVE_OUTCOME_RELABELLING", "OUTCOME_LEAKAGE_INTO_PROSPECTIVE_DESIGN")) else "PASS"
    if invalid:
        return _out("CONTRACT_INVALID", invalid, gates)

    # Facts and prose (or two reviewers) disagree: no label beyond INSUFFICIENT is defensible.
    if att["status"] == "CONTESTED":
        return _out("INSUFFICIENT_INFORMATION", ["FACTS_CONTRADICTION_UNRESOLVED"], gates)
    missing = []

    # (2) STRUCTURAL_TEST: scoped structural contract with both controls (checked above).
    if kind == "STRUCTURAL":
        gates.update(G1="PASS", G6="PASS", G2="NOT_APPLICABLE", G3="NOT_APPLICABLE", G4="NOT_APPLICABLE", G5="NOT_APPLICABLE")
        return _out("STRUCTURAL_TEST", ["THREAT_COVERAGE_LIMITED"], gates)
    gates.update(G1="PASS", G6="NOT_APPLICABLE")

    # (3) NONDISCRIMINATING_ENDPOINT: an admissible bound proves the threshold unreachable.
    admissible = bnd["kind"] in ("ANALYTIC", "INDEPENDENT_CALIBRATION") or (
        bnd["kind"] == "OBSERVED_OUTCOME" and not prospective)
    if admissible and _num(bnd["max_abs_contrast"]) and _num(bnd["threshold"]) and bnd["threshold"] > bnd["max_abs_contrast"]:
        if corroborated and att["status"] == "ATTESTED":
            gates["G2"] = "FAIL"
            return _out("NONDISCRIMINATING_ENDPOINT", ["DECLARED_BOUND_PRECLUDES_MARGIN"], gates)
        # spec D4: an unbacked or unattested bound can't prove impossibility, and a blocked
        # ND candidate stops here: lower-precedence labels (DEMONSTRATION) must not override it.
        blocked = ([] if corroborated else ["BOUND_NOT_CORROBORATED"]) + ([] if att["status"] == "ATTESTED" else ["FACTS_UNATTESTED"])
        gates["G2"] = "UNKNOWN"
        return _out("INSUFFICIENT_INFORMATION", ["ND_CANDIDATE_NOT_ESTABLISHED"] + blocked, gates)

    # (4) DEMONSTRATION: known/trivial comparison as framed.
    if cmp_["contribution"] == "NOVEL_ADVANTAGE" and cmp_["strength"] == "TRIVIAL_FLOOR_ONLY":
        gates["G3"] = "FAIL"
        return _out("DEMONSTRATION", ["WEAK_COMPARATOR_FOR_CLAIM"], gates)
    if cmp_["contribution"] == "NOVEL_ADVANTAGE" and fc["status"] == "ANALYTICALLY_PREDICTABLE":
        gates["G4"] = "FAIL"
        return _out("DEMONSTRATION", ["RESULT_ANALYTICALLY_IMPLIED"], gates)
    if cmp_["contribution"] == "DEMONSTRATION":
        return _out("DEMONSTRATION", ["DECLARED_DEMONSTRATION"], gates)

    # (5) INSUFFICIENT_INFORMATION: every unmet readiness condition is listed.
    if att["status"] != "ATTESTED":
        missing.append("FACTS_UNATTESTED")
    if not corroborated:
        missing.append("BOUND_NOT_CORROBORATED")
    if ora["label_oracle_role"] == "USED_AS_HEADROOM_EVIDENCE":
        missing.append("ORACLE_LEAKAGE_TO_HEADROOM_ARGUMENT")
    if not prospective:
        missing.append("RETROSPECTIVE_NOT_READINESS")
    if kind != "COMPARATIVE_EFFECT":
        missing.append("READINESS_REQUIRES_COMPARATIVE_CLAIM")
    if bnd["kind"] == "OBSERVED_PILOT":
        missing.append("PILOT_NOT_ANALYTIC_BOUND")
    if bnd["kind"] not in ("ANALYTIC", "INDEPENDENT_CALIBRATION"):
        missing.append("CONTRAST_BOUND_NOT_ESTABLISHED")
    if cmp_["strength"] != "STRONG_PRIOR_ART":
        missing.append("STRONG_BASELINE_UNRESOLVED")
    if fc["status"] != "PREDECLARED_FORECAST":
        missing.append("FORECAST_NOT_ESTABLISHED")
    if pr["status"] != "ESTIMATED":
        missing.append("PRECISION_NOT_ESTABLISHED")
    if pr["calibration_disjoint"] != "YES":
        missing.append("CALIBRATION_SEPARATION_NOT_ESTABLISHED")
    if not (isinstance(pr["independent_units"], int) and pr["independent_units"] >= 2):
        missing.append("INDEPENDENT_UNITS_NOT_ESTABLISHED")
    if not (_num(pr["mde"]) and _num(pr["min_effect"]) and pr["mde"] <= pr["min_effect"]):
        missing.append("MDE_ABOVE_MEANINGFUL_EFFECT_OR_UNKNOWN")
    if missing:
        gates.update(G5="UNKNOWN")
        return _out("INSUFFICIENT_INFORMATION", missing, gates)

    # (6) READY_FOR_COMPARISON: every condition affirmatively declared.
    gates.update(G2="PASS", G3="PASS", G4="PASS", G5="PASS")
    return _out("READY_FOR_COMPARISON", ["PROSPECTIVE_REQUIREMENTS_DECLARED"], gates)
