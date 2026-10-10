"""Build visible_cases_v02.json from the v0.1 visible cases (PR #20) plus typed facts.

Each V-case keeps its v0.1 prose and expected label unchanged; only a `facts` block is added,
encoding what that prose declares. F-cases flip one fact on the READY base to show each
decisive fact changes the label (anti-vacuity for the checker).
Written by Claude (Opus 5.5), 2026-10-09. Usage: python3 -I build_cases_v02.py ../tests/dpc001/visible_cases.json
"""
import copy, json, sys

v01 = json.load(open(sys.argv[1], encoding="utf-8"))
base = copy.deepcopy(v01["base_contract"])
base["schema"] = "dpc-study-v0.2"
base["facts"] = {
    "registration": {"relabels_registered_outcome": False, "outcome_informed_design_choice": False},
    "construct": {"structural_scope": "NOT_STRUCTURAL", "structural_includes_rate_claim": False,
                  "rate_population": "NOT_A_RATE_CLAIM", "rate_generalized_beyond_sample": False},
    "oracle": {"policy_inputs_include_eval_labels": False, "label_oracle_role": "NONE"},
    "bound": {"kind": "ANALYTIC", "max_abs_contrast": 20, "threshold": 1.0, "units": "rewards per 200 pulls"},
    "comparator": {"strength": "STRONG_PRIOR_ART", "contribution": "NOVEL_ADVANTAGE"},
    "forecast": {"status": "PREDECLARED_FORECAST"},
    "precision": {"status": "ESTIMATED", "mde": 0.84, "min_effect": 1.0, "calibration_disjoint": "YES", "independent_units": 400,
                  "units": "rewards per 200 pulls"},
    "controls": {"positive": True, "negative": True},
    "attestation": {"status": "ATTESTED", "bound_artifact": "experiments/example/BOUND_DERIVATION.md@1111111 (illustrative fixture)"},
}
STRUCT = {"construct": {"structural_scope": "ENUMERATED"}, "comparator": {"strength": "NOT_APPLICABLE_STRUCTURAL", "contribution": "CORRECTNESS"},
          "forecast": {"status": "NOT_APPLICABLE"}, "bound": {"kind": "NONE", "max_abs_contrast": "NOT_APPLICABLE", "threshold": "NOT_APPLICABLE"},
          "precision": {"status": "NOT_APPLICABLE_STRUCTURAL", "mde": "NOT_APPLICABLE", "min_effect": "NOT_APPLICABLE",
                        "calibration_disjoint": "NOT_APPLICABLE", "independent_units": "NOT_APPLICABLE"}}
UNK = {"status": "UNKNOWN", "mde": "UNKNOWN", "calibration_disjoint": "UNKNOWN"}


def deep(a, b):
    out = copy.deepcopy(a)
    for k, v in b.items():
        out[k] = deep(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else copy.deepcopy(v)
    return out


FACTS = {  # what each v0.1 case's prose declares, as typed facts
    "V01": {"bound": {"kind": "OBSERVED_OUTCOME", "max_abs_contrast": 0, "threshold": 1}},
    "V02": {"bound": {"kind": "NONE", "max_abs_contrast": "UNKNOWN", "threshold": 1}, "forecast": {"status": "UNAVAILABLE"}, "precision": UNK},
    "V03": {"comparator": {"strength": "TRIVIAL_FLOOR_ONLY"}, "forecast": {"status": "ANALYTICALLY_PREDICTABLE"},
            "bound": {"max_abs_contrast": 30, "threshold": 5}, "precision": {"min_effect": 5}},
    "V04": STRUCT, "V05": STRUCT,
    "V06": deep(STRUCT, {"controls": {"positive": False}}),
    "V07": deep(STRUCT, {"construct": {"structural_scope": "BROAD"}}),
    "V08": {"oracle": {"label_oracle_role": "USED_AS_HEADROOM_EVIDENCE"}, "bound": {"kind": "OBSERVED_OUTCOME", "max_abs_contrast": 4.358, "threshold": 1.0}},
    "V09": {"oracle": {"policy_inputs_include_eval_labels": True, "label_oracle_role": "CLAIMED_ACHIEVABLE"}},
    "V10": {"construct": {"rate_population": "CONSTRUCTED_NOT_SAMPLED", "rate_generalized_beyond_sample": True}},
    "V11": STRUCT,
    "V12": {"bound": {"kind": "OBSERVED_OUTCOME", "max_abs_contrast": "UNKNOWN", "threshold": "UNKNOWN"}, "precision": dict(UNK, min_effect="UNKNOWN")},
    "V13": {}, "V14": {"forecast": {"status": "UNAVAILABLE"}, "precision": UNK}, "V15": {},
    "V16": {"comparator": {"contribution": "REPLICATION"}},
    "V17": {"bound": {"threshold": 25}},
    "V18": {"bound": {"kind": "OBSERVED_PILOT", "max_abs_contrast": "UNKNOWN"}, "precision": UNK},
    "V19": deep(STRUCT, {"construct": {"structural_includes_rate_claim": True}}),
    "V20": {"registration": {"relabels_registered_outcome": True}},
}
cases = []
for c in v01["cases"]:
    c = copy.deepcopy(c)
    c["overrides"]["facts"] = FACTS[c["id"]]
    cases.append(c)

F = [  # one fact flipped on the READY base
    ("F01", "CONTRACT_INVALID", {"oracle": {"label_oracle_role": "CLAIMED_ACHIEVABLE"}}),
    ("F02", "CONTRACT_INVALID", {"oracle": {"policy_inputs_include_eval_labels": True}}),
    ("F03", "CONTRACT_INVALID", {"registration": {"outcome_informed_design_choice": True}}),
    ("F04", "CONTRACT_INVALID", {"bound": {"kind": "OBSERVED_OUTCOME"}}),
    ("F05", "INSUFFICIENT_INFORMATION", {"comparator": {"strength": "UNRESOLVED"}}),
    ("F06", "DEMONSTRATION", {"comparator": {"strength": "TRIVIAL_FLOOR_ONLY"}}),
    ("F07", "DEMONSTRATION", {"forecast": {"status": "ANALYTICALLY_PREDICTABLE"}}),
    ("F08", "INSUFFICIENT_INFORMATION", {"precision": {"mde": 1.5}}),
    ("F09", "INSUFFICIENT_INFORMATION", {"precision": {"calibration_disjoint": "NO"}}),
    ("F10", "NONDISCRIMINATING_ENDPOINT", {"bound": {"threshold": 25}}),
    ("F11", "READY_FOR_COMPARISON", {"oracle": {"label_oracle_role": "OPTIMISTIC_BOUND_ONLY"}}),
    ("F12", "CONTRACT_INVALID", None),
    ("F13", "CONTRACT_INVALID", {"bound": {"max_abs_contrast": "20"}}),
    ("F14", "INSUFFICIENT_INFORMATION", {"comparator": {"strength": "TRIVIAL_FLOOR_ONLY", "contribution": "REPLICATION"}}),
    ("F15", "INSUFFICIENT_INFORMATION", {"forecast": {"status": "UNCERTAIN"}}),
    ("F16", "CONTRACT_INVALID", {"construct": {"structural_scope": "ENUMERATED"}}),
    # Round 2, added after ChatGPT's review of 65c421a (PR #25 comment 6091333519), registered before running:
    ("A01", "CONTRACT_INVALID", {"controls": {"positive": [True]}}),                       # nested list where bool expected
    ("A02", "CONTRACT_INVALID", {"bound": {"max_abs_contrast": {"value": 20}}}),            # nested object where number expected
    ("A03", "CONTRACT_INVALID", {"bound": {"max_abs_contrast": float("nan")}}),
    ("A04", "CONTRACT_INVALID", {"bound": {"threshold": float("inf")}}),
    ("A05", "CONTRACT_INVALID", {"bound": {"max_abs_contrast": -5}}),                       # negative bound
    ("A06", "CONTRACT_INVALID", {"bound": {"threshold": 0}}),                               # zero margin
    ("A07", "CONTRACT_INVALID", {"precision": {"independent_units": 0}}),
    ("A08", "CONTRACT_INVALID", {"precision": {"mde": -0.5}}),
    ("A09", "CONTRACT_INVALID", {"construct": {"structural_includes_rate_claim": True}}),    # rate flag on a comparative claim
    ("A10", "CONTRACT_INVALID", {"extra_unchecked_flag": True}),                            # unknown facts key: strict schema
    ("A11", "CONTRACT_INVALID", {"bound": {"units": ""}}),
    ("A12", "INSUFFICIENT_INFORMATION", {"attestation": {"status": "UNATTESTED"}}),          # READY needs attested facts
    ("A13", "INSUFFICIENT_INFORMATION", {"attestation": {"status": "CONTESTED"}}),           # facts vs prose disagreement
    ("A14", "INSUFFICIENT_INFORMATION", {"attestation": {"bound_artifact": "NONE"}}),        # READY needs a backed bound
    ("A15", "INSUFFICIENT_INFORMATION", {"bound": {"threshold": 25}, "attestation": {"bound_artifact": "NONE"}}),  # unbacked bound can't prove ND
    ("A16", "INSUFFICIENT_INFORMATION", {"bound": {"kind": "OBSERVED_PILOT"}}),             # ANALYTIC swapped for a pilot
    # Added after ChatGPT's follow-up (comment 6091374834): spec D4 says ND also needs ATTESTED.
    ("A17", "INSUFFICIENT_INFORMATION", {"bound": {"threshold": 25}, "attestation": {"status": "UNATTESTED"}}),
]
for fid, exp, fo in F:
    cases.append({"id": fid, "expect": exp, "spec_ref": "v0.2 fact-flip on V15" if fid[0] == "F" else "v0.2 adversarial (ChatGPT review)",
                  "overrides": {"facts": fo}})

out = {k: v for k, v in v01.items() if k not in ("base_contract", "cases", "spec")}
out["spec"] = {"path": "coordination/dpc001_v02/SPEC_V02_DRAFT.md", "status": "DRAFT_NOT_FROZEN", "derived_from_v01_commit": v01["spec"]["commit"]}
out["base_contract"] = base
out["cases"] = cases
json.dump(out, open("visible_cases_v02.json", "w", encoding="utf-8", newline="\n"), indent=1, ensure_ascii=False, allow_nan=True)
print(f"wrote {len(cases)} cases")
