"""Paraphrase robustness probe for a DPC-001 checker (Claude review, 2026-10-09).
Each probe rewrites ONLY wording in a VISIBLE case, keeping its meaning, so the
expected label is unchanged. Predictions registered before the first run:
a checker that understands the rule keeps every label; a phrase-matcher flips some.
Control probes C* change nothing meaningful and must keep their label.
Usage: python3 -I paraphrase_probe.py path/to/checker.py:classify visible_cases.json
Written by Claude (Opus 5.5) as a review tool; uses visible cases only."""
import argparse, copy, importlib.util, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_acceptance import merge  # same merge rule as the harness

P = [  # (probe id, visible case, dotted field, new text)
 ("P1", "V03", "comparators.primary_strong_baseline", "always pull the middle arm (expected 50/100)"),
 ("P1", "V03", "comparators.baseline_selection_reason", "easy-to-compute reference policies"),
 ("P2", "V09", "design.policy_inputs_allowed", "model outputs at each depth and whether each depth's answer was right"),
 ("P3", "V08", "feasibility.contrast_bound", "a per-instance oracle that picks depth using the ground-truth answers of the test set reaches +4.358 pp over the shuffle"),
 ("P3", "V08", "feasibility.forecast_input_provenance", "the oracle reads the test-set answers"),
 ("P4", "V20", "claim.hypothesis", "ITC-001 H2 holds after dropping the parity8 task"),
 ("P4", "V20", "claim.intended_contribution", "updated verdict on a registered hypothesis"),
 ("P5", "V10", "design.task_distribution", "all 512 episodes were built to contain the same poisoned anchor"),
 ("P5", "V10", "claim.hypothesis", "evidence-first fusion accepts a poisoned trusted anchor 100% of the time in real multiagent systems"),
 ("P6", "V17", "feasibility.contrast_bound", "the paired difference cannot exceed 20 rewards in absolute value (200 x (0.55-0.45)); the registered +25 margin is above that"),
 ("C1", "V15", None, None),
 ("C2", "V03", None, None),
]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("checker"); ap.add_argument("cases"); a = ap.parse_args()
    path, fn = a.checker.rsplit(":", 1)
    spec = importlib.util.spec_from_file_location("chk", path); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    d = json.load(open(a.cases, encoding="utf-8")); base = d["base_contract"]; by = {c["id"]: c for c in d["cases"]}
    probes = {}
    for pid, cid, field, text in P:
        probes.setdefault(pid, [cid, copy.deepcopy(by[cid]["overrides"])])
        if field:
            o = probes[pid][1]; *head, last = field.split(".")
            for h in head: o = o.setdefault(h, {})
            o[last] = text
    kept = 0
    for pid, (cid, over) in probes.items():
        got = getattr(mod, fn)(merge(base, over))["primary"]; exp = by[cid]["expect"]; ok = got == exp; kept += ok
        print(f"{'KEPT ' if ok else 'FLIP '} {pid} (from {cid})  expected {exp:<27} got {got}")
    print(f"\nVERDICT  {kept} of {len(probes)} probes kept their label")
    return 0 if kept == len(probes) else 1

sys.exit(main())
