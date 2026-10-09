"""DPC-001 prospective design precheck, experimental rule-based reference.

Scope: classify *declared study contracts*, not results or permissions to run.
No network, filesystem reads, execution of study code, or access to withheld tests.
Rules are conservative heuristics for natural-language contract fields. In particular,
they do NOT prove statistical power, provenance, truth, or novel contribution.
"""
from __future__ import annotations

import re
from typing import Any

LABELS = (
    "CONTRACT_INVALID", "STRUCTURAL_TEST", "NONDISCRIMINATING_ENDPOINT",
    "DEMONSTRATION", "INSUFFICIENT_INFORMATION", "READY_FOR_COMPARISON",
)
REQUIRED = {
    "source": ("repository", "revision_sha", "protocol_path", "protocol_sha256",
               "fixture_or_generator_revision", "evidence_provenance"),
    "claim": ("claim_kind", "hypothesis", "intended_contribution",
              "primary_endpoint", "unit_of_analysis", "denominator", "direction",
              "success_threshold", "minimum_meaningful_effect"),
    "design": ("task_distribution", "policy_inputs_allowed", "protected_oracle",
               "calibration_data", "evaluation_data", "resources", "stop_rule"),
    "comparators": ("primary_strong_baseline", "baseline_selection_reason",
                    "omitted_competitors", "trivial_floor_controls"),
    "feasibility": ("contrast_bound", "forecast_method", "forecast_input_provenance",
                    "planned_precision", "assumptions_and_failure_modes"),
    "threat_scope": ("tested_mechanism_or_attack", "positive_control", "negative_control"),
}
UNKNOWN = re.compile(r"\b(unknown|unavailable|unresolved|not supplied|not estimated|none available|no analysis)\b", re.I)


def _s(v: Any) -> str:
    if isinstance(v, str):
        return v.lower()
    return "" if v is None else str(v).lower()


def _missing(v: Any) -> bool:
    return v is None or (isinstance(v, str) and not v.strip())


def _unresolved(v: Any) -> bool:
    return _missing(v) or bool(UNKNOWN.search(_s(v)))


def _out(primary: str, *reasons: str, **other: Any) -> dict[str, Any]:
    return {"primary": primary, "reason_codes": list(dict.fromkeys(reasons)),
            "limitations": ["Heuristic natural-language design review; not proof of scientific validity."],
            "replay_status": "NOT_RUN", **other}


def _get(d: dict[str, Any], section: str, key: str) -> Any:
    part = d.get(section)
    return part.get(key) if isinstance(part, dict) else None


def _structural_scope_broad(claim: str, mechanism: str) -> bool:
    broad = bool(re.search(r"\b(all|every|any|99%|100%|real deployments|in deployments|universal)\b", claim))
    scoped = bool(re.search(r"\b(only|single|one|fixed|fixture|specific|registered|planted)\b", mechanism))
    mechanism_broad = bool(re.search(r"\b(all|every|any)\b.*\b(attacks|retries|deployments|cases)\b", mechanism))
    return mechanism_broad or (broad and not scoped)


def _analytic_impossibility(bound: str, threshold: str, phase: str) -> bool:
    if phase != "RETROSPECTIVE_DIAGNOSTIC" and re.search(r"\b(pilot|observed|5.seed|small sample)\b", bound):
        return False
    if phase == "RETROSPECTIVE_DIAGNOSTIC" and ("ceiling" in bound or "saturat" in bound):
        return True
    # A stated interval is treated only as a *declared* mathematical bound,
    # never independently proven from free text.
    match = re.search(r"\[\s*([+-]?\d+(?:\.\d+)?)\s*,\s*([+-]?\d+(?:\.\d+)?)\s*\]", bound)
    target = re.search(r"(?:>=|>|at least|minimum)\s*\+?([\d.]+)", threshold)
    if match and target and ("possible" in bound or "bound" in bound):
        return float(target.group(1)) > float(match.group(2))
    return False


def classify(contract: dict[str, Any]) -> dict[str, Any]:
    """Return a single primary disposition and explanatory reason codes.

    Classification is advisory. The caller must not turn READY into authorization.
    """
    if not isinstance(contract, dict) or contract.get("schema") != "dpc-study-v0.1":
        return _out("CONTRACT_INVALID", "SCHEMA_INVALID")
    if _missing(contract.get("study_id")):
        return _out("CONTRACT_INVALID", "STUDY_ID_MISSING")
    phase = contract.get("review_phase")
    if phase not in ("PROSPECTIVE", "RETROSPECTIVE_DIAGNOSTIC"):
        return _out("CONTRACT_INVALID", "REVIEW_PHASE_INVALID")
    for section, keys in REQUIRED.items():
        part = contract.get(section)
        if section == "comparators" and contract.get("claim", {}).get("claim_kind") == "STRUCTURAL":
            if part == "NOT_APPLICABLE_STRUCTURAL":
                continue
        if not isinstance(part, dict):
            return _out("CONTRACT_INVALID", "SECTION_MISSING_" + section.upper())
        for key in keys:
            if key not in part or _missing(part[key]):
                return _out("CONTRACT_INVALID", "REQUIRED_FIELD_MISSING", section.upper() + "_" + key.upper())

    claim = contract["claim"]
    design = contract["design"]
    feas = contract["feasibility"]
    scope = contract["threat_scope"]
    cmp = contract["comparators"]
    kind = claim["claim_kind"]
    if kind not in ("STRUCTURAL", "DESCRIPTIVE_RATE", "COMPARATIVE_EFFECT"):
        return _out("CONTRACT_INVALID", "CLAIM_KIND_INVALID")
    text_claim = " ".join(_s(claim[k]) for k in ("hypothesis", "intended_contribution",
                                                 "primary_endpoint", "denominator", "success_threshold"))
    mechanism = _s(scope["tested_mechanism_or_attack"])
    permitted = _s(design["policy_inputs_allowed"])
    oracle = _s(design["protected_oracle"])
    bound = _s(feas["contrast_bound"])
    provenance = _s(feas["forecast_input_provenance"])

    # G0/G1: contradictory or retrospective result rewriting cannot be blessed.
    if phase == "RETROSPECTIVE_DIAGNOSTIC" and re.search(
        r"\b(supported once|now supported|revised status|exclude.{0,30}parity8)\b", text_claim
    ):
        return _out("CONTRACT_INVALID", "RETROSPECTIVE_OUTCOME_RELABELLING")
    if kind == "STRUCTURAL":
        if re.search(r"\b(99%|100%|failure rate|deployment rate|real deployments)\b", text_claim):
            return _out("CONTRACT_INVALID", "STRUCTURAL_RATE_CONFLATION")
        if _missing(scope["positive_control"]) or _missing(scope["negative_control"]):
            return _out("CONTRACT_INVALID", "STRUCTURAL_CONTROL_MISSING")
        if _structural_scope_broad(text_claim, mechanism):
            return _out("CONTRACT_INVALID", "THREAT_SCOPE_UNSUPPORTED")
        reasons = []
        if re.search(r"\b(only|single|one|specific|fixed|fixture)\b", mechanism):
            reasons.append("THREAT_COVERAGE_LIMITED")
        return _out("STRUCTURAL_TEST", *reasons, claim_kind=kind, review_phase=phase)

    if kind == "DESCRIPTIVE_RATE" and (
        "every episode deliberately" in _s(design["task_distribution"])
        or "constructed" in _s(design["task_distribution"])
    ) and ("deployment" in text_claim or "real.world" in text_claim):
        return _out("CONTRACT_INVALID", "SYNTHETIC_RATE_EXTRAPOLATION")

    # G2: do not mistake optimistic hindsight label-oracle bounds for feasible policies.
    label_oracle = bool(re.search(r"(true labels?|held.out true labels?|evaluation labels?|correctness of each depth)", bound + " " + provenance + " " + permitted))
    if label_oracle:
        if "correctness of each depth" in permitted or ("achievable" in bound and "oracle" in bound):
            return _out("CONTRACT_INVALID", "ORACLE_MISREPRESENTED_AS_FEASIBLE")
        return _out("INSUFFICIENT_INFORMATION", "ORACLE_LEAKAGE_TO_HEADROOM_ARGUMENT")

    if _analytic_impossibility(bound, _s(claim["success_threshold"]), phase):
        return _out("NONDISCRIMINATING_ENDPOINT", "DECLARED_BOUND_PRECLUDES_MARGIN")

    # G3/G4: known examples with inadequate rivals cannot substantiate a superiority claim.
    if isinstance(cmp, dict):
        baseline = _s(cmp["primary_strong_baseline"])
        floor = _s(cmp["trivial_floor_controls"])
        selection = _s(cmp["baseline_selection_reason"])
        contribution = _s(claim["intended_contribution"])
        weak_only = ("fixed.medium" in baseline or "uniform random" in baseline or
                     ("simple reference" in selection and "random" in floor))
        if weak_only and ("advantage" in contribution or "superior" in contribution):
            return _out("DEMONSTRATION", "WEAK_COMPARATOR_FOR_CLAIM")

    # G2/G5: uncertain precision or a pilot do not prove unreachability.
    required_info = [feas.get("contrast_bound"), feas.get("planned_precision"),
                     feas.get("forecast_method"), feas.get("forecast_input_provenance"),
                     design.get("evaluation_data"), claim.get("unit_of_analysis"),
                     claim.get("denominator")]
    if any(_unresolved(i) for i in required_info):
        return _out("INSUFFICIENT_INFORMATION", "MANDATORY_FEASIBILITY_UNKNOWN")
    if isinstance(cmp, dict):
        if any(_unresolved(cmp.get(key)) for key in (
            "primary_strong_baseline", "baseline_selection_reason", "omitted_competitors"
        )):
            return _out("INSUFFICIENT_INFORMATION", "STRONG_BASELINE_UNRESOLVED")
    if "pilot" in bound and ("claimed" in bound or "prove" in bound):
        return _out("INSUFFICIENT_INFORMATION", "PILOT_NOT_ANALYTIC_BOUND")

    return _out("READY_FOR_COMPARISON", "PROSPECTIVE_REQUIREMENTS_DECLARED",
                claim_kind=kind, review_phase=phase)
