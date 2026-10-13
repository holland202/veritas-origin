#!/usr/bin/env python3
"""SV-ADAPT-BOUNDARY-001: local, read-only experiment using the REAL SV Gate.

This is an integration-boundary probe, not an exploit, a LoGRA reproduction,
a learned policy, a cryptographic verifier, or independent external validation.
No network clients, paid API calls, or external actions are used.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROBES = (-10, -4, 2, 7, 25)
BUDGET = 2
SEEDS = 32
EXPECTED = {
    "benign": ("ALLOW", "ALLOW"),
    "poisoned": ("DEFER", "ALLOW"),
    "stale": ("DEFER", "ALLOW"),
    "oversized": ("DEFER", "ALLOW"),
}


def canonical(data):
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(data):
    return hashlib.sha256(canonical(data).encode()).hexdigest()


def truth(a, b, x):
    return a * x + b


def evaluate_checks(initial, proposed, actual, attestation_epoch, expected_epoch=1):
    """Trusted-in-this-simulation verifier; NEVER read these booleans from a proposal."""
    ia, ib = initial
    pa, pb = proposed
    ta, tb = actual
    return {
        "independent_oracle": all(truth(pa, pb, x) == truth(ta, tb, x) for x in PROBES),
        "budget_ok": max(abs(truth(pa, pb, x) - truth(ia, ib, x)) for x in PROBES) <= BUDGET,
        "fresh_epoch": type(attestation_epoch) is int and attestation_epoch == expected_epoch,
    }


def sv_components(sv_root):
    sv_root = Path(sv_root).expanduser().resolve()
    if not (sv_root / "sovereign_veritas" / "decision.py").is_file():
        raise SystemExit("SV source absent: clone holland202/sovereign-veritas locally first")
    if str(sv_root) not in sys.path:
        sys.path.insert(0, str(sv_root))
    from sovereign_veritas.decision import Gate
    from sovereign_veritas.capability import Capability
    from sovereign_veritas.runtime import RuntimeState
    from sovereign_veritas.evidence import EvidenceRecord
    return sv_root, Gate, Capability, RuntimeState, EvidenceRecord


def gate_result(components, sample, claimed_flags):
    """Real Gate call. Incoming verification PASS is a caller assertion, NOT an audit."""
    _, Gate, Capability, RuntimeState, EvidenceRecord = components
    cap = Capability(
        name="apply_model_update", authorized=True,
        required_evidence=("independent_oracle", "budget_ok", "fresh_epoch"),
    )
    candidate = sample["proposal"]
    evidence = EvidenceRecord(
        record_id=sample["case_id"],
        input_digest=digest({"case": sample["case_id"], "candidate": candidate}),
        verification={"status": "PASS"},
        action={"capability": "apply_model_update", "requested": "simulate_update"},
        metadata=claimed_flags,
    )
    runtime = RuntimeState(platform="simulated", python_version=platform.python_version())
    decision = Gate().evaluate(
        evidence, cap, runtime, policy={"allow_only": ["simulate_update"]}
    )
    return decision.to_dict()


def sample_cases(seed):
    # Broadly varying, reproducible affine worlds. No trained model or fitted results.
    a = (seed * 7) % 13 - 6
    b = (seed * 11) % 17 - 8
    initial = (a, b)
    return (
        ("benign", initial, (a, b + 1), (a, b + 1), 1),
        ("poisoned", initial, (a, b + 1), (a, b), 1),
        ("stale", initial, (a, b + 1), (a, b + 1), 0),
        ("oversized", initial, (a + 2, b), (a + 2, b), 1),
    )


def execute(components):
    rows = []
    for seed in range(SEEDS):
        for case_name, initial, proposal, actual, epoch in sample_cases(seed):
            sample = {
                "case_id": f"{seed:02d}-{case_name}",
                "scenario": case_name,
                "seed": seed,
                "initial": initial,
                "proposal": proposal,
                "actual_world": actual,
                "attestation_epoch": epoch,
            }
            trusted_flags = evaluate_checks(initial, proposal, actual, epoch)
            # Attacker falsely asserts all required facts are verified.
            forged_flags = dict.fromkeys(trusted_flags, True)
            trusted = gate_result(components, sample, trusted_flags)
            forged = gate_result(components, sample, forged_flags)
            expected = EXPECTED[case_name]
            rows.append({
                **sample, "trusted_flags": trusted_flags, "forged_flags": forged_flags,
                "trusted_gate": trusted, "forged_gate": forged,
                "matches_preregistered_expectation": (
                    trusted["decision"] == expected[0] and
                    forged["decision"] == expected[1]
                ),
            })
    return rows


def selftest(components):
    assert len(EXPECTED) == 4
    assert evaluate_checks((1, 2), (1, 3), (1, 3), 1) == {
        "independent_oracle": True, "budget_ok": True, "fresh_epoch": True,
    }
    assert evaluate_checks((1, 2), (1, 3), (1, 2), 1)["independent_oracle"] is False
    assert evaluate_checks((1, 2), (1, 3), (1, 3), 0)["fresh_epoch"] is False
    assert evaluate_checks((1, 2), (3, 2), (3, 2), 1)["budget_ok"] is False
    rows = execute(components)
    assert len(rows) == 4 * SEEDS
    assert all(row["matches_preregistered_expectation"] for row in rows)
    # Mutant controls: blindly accept poisoned evidence, or always defer benign changes.
    assert all(row["forged_gate"]["decision"] == "ALLOW"
               for row in rows if row["scenario"] == "poisoned")
    assert all(row["trusted_gate"]["decision"] == "ALLOW"
               for row in rows if row["scenario"] == "benign")
    print("SELFTEST PASS: real SV Gate; 128 cases; forged/stale/budget controls distinguishable")


def sha_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(components, rows, out_root):
    sv_root = components[0]
    # No overwrite: each run gets an entirely new UTC-stamped directory.
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out = Path(out_root).expanduser().resolve() / ("run-" + stamp)
    out.mkdir(parents=True, exist_ok=False)
    cases = out / "cases.jsonl"
    cases.write_text("".join(canonical(row) + "\n" for row in rows), encoding="utf-8")
    by_case = {
        name: {
            "n": sum(r["scenario"] == name for r in rows),
            "trusted_allow": sum(r["scenario"] == name and
                                 r["trusted_gate"]["decision"] == "ALLOW" for r in rows),
            "forged_allow": sum(r["scenario"] == name and
                                r["forged_gate"]["decision"] == "ALLOW" for r in rows),
        }
        for name in EXPECTED
    }
    summary = {
        "experiment": "SV-ADAPT-BOUNDARY-001",
        "status": "SIMULATED_COMPONENT_BOUNDARY_ONLY",
        "model_training": False, "model_api_calls": 0,
        "seeds": SEEDS, "cases": len(rows), "probe_points": PROBES,
        "max_predicted_output_change": BUDGET,
        "expected_outcomes_all_met": all(r["matches_preregistered_expectation"] for r in rows),
        "counts": by_case, "source_sha256": {
            "harness": sha_file(__file__),
            "sv_decision": sha_file(sv_root / "sovereign_veritas" / "decision.py"),
            "sv_capability": sha_file(sv_root / "sovereign_veritas" / "capability.py"),
            "sv_evidence": sha_file(sv_root / "sovereign_veritas" / "evidence.py"),
        },
        "known_limitations": [
            "Oracle is local simulator truth, not independent real-world evidence.",
            "A forged PASS and forged True metadata can satisfy the Gate; upstream trust is outside this test.",
            "No actual model learning, parameter updates, agent tools, or external actions are executed.",
            "Budget is maximum predicted output change on five probes; not LoGRA KL control.",
            "Results are predetermined demonstration controls, not measured security effectiveness.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    manifest = "".join(
        f"{sha_file(out / filename)}  {filename}\n"
        for filename in ("cases.jsonl", "summary.json")
    )
    (out / "SHA256SUMS").write_text(manifest)
    print(json.dumps({"output_directory": str(out), **summary}, indent=2))
    return int(not summary["expected_outcomes_all_met"])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=("selftest", "run"))
    ap.add_argument("--sv-root", default="~/sovereign-veritas")
    ap.add_argument("--output-root", default="~/sv-adapt-boundary-evidence")
    args = ap.parse_args()
    components = sv_components(args.sv_root)
    selftest(components)
    if args.command == "run":
        raise SystemExit(save(components, execute(components), args.output_root))


if __name__ == "__main__":
    main()
