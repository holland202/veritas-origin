"""Prose-invariance test for any DPC-001 checker.

For every case, rewrites every free-text field in the six prose sections, keeping the
fields non-empty, and requires the checker's primary label to stay the same. Two rewrites:
  blank  - every prose string becomes "text rewritten for invariance test"
  borrow - every prose string is taken from a different case (rotation by 7)
A checker that decides from typed facts passes both. A checker that reads phrases fails.
Run it on PR #24's v0.1 checker to see the test fail (anti-vacuity).
Written by Claude (Opus 5.5), 2026-10-09.
Usage: python3 -I prose_invariance.py path/checker.py:classify cases.json
"""
import argparse, copy, importlib.util, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_acceptance import merge

SECTIONS = ("source", "claim", "design", "comparators", "feasibility", "threat_scope")
KEEP = {("claim", "claim_kind")}  # an enum, not prose


def prose_paths(c):
    for s in SECTIONS:
        if isinstance(c.get(s), dict):
            for k, v in c[s].items():
                if isinstance(v, str) and (s, k) not in KEEP:
                    yield s, k


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("checker"); ap.add_argument("cases"); a = ap.parse_args()
    path, fn = a.checker.rsplit(":", 1)
    spec = importlib.util.spec_from_file_location("chk", path); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    classify = getattr(mod, fn)
    d = json.load(open(a.cases, encoding="utf-8"))
    contracts = [(c["id"], merge(d["base_contract"], c["overrides"])) for c in d["cases"]]
    held, total = 0, 0
    for i, (cid, c) in enumerate(contracts):
        want = classify(copy.deepcopy(c))["primary"]
        donor = contracts[(i + 7) % len(contracts)][1]
        for mode in ("blank", "borrow"):
            x = copy.deepcopy(c)
            for s, k in prose_paths(x):
                d_val = donor.get(s, {}).get(k) if isinstance(donor.get(s), dict) else None
                x[s][k] = "text rewritten for invariance test" if mode == "blank" or not isinstance(d_val, str) or not d_val.strip() else d_val
            got = classify(x)["primary"]; total += 1; ok = got == want; held += ok
            if not ok:
                print(f"CHANGED  {cid:<4} {mode:<6} {want} -> {got}")
    print(f"\nVERDICT  {held} of {total} rewrites kept the label")
    return 0 if held == total else 1


sys.exit(main())
