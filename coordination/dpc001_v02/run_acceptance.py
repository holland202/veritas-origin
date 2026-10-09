#!/usr/bin/env python3
"""DPC-001 acceptance harness (test side only; contains no checker logic).

A checker must expose  classify(contract: dict) -> {"primary": <one of the six labels>, "reason_codes": [str, ...]}.

  python3 -I run_acceptance.py --checker path/to/checker.py:classify visible_cases.json [withheld_cases.json]
  python3 -I run_acceptance.py --mutant always_ready visible_cases.json        # built-in trivial checkers;
  python3 -I run_acceptance.py --mutant always_insufficient visible_cases.json  # the suite must FAIL each one
Exit 0 only if every case's primary label matches and every listed reason code is present.
Written by Claude (Opus 5.5) from the frozen DPC-001 spec (sha256 c02a1daa...cf9); not reviewed line by line by Chad.
"""
import argparse, copy, importlib.util, json, sys
from collections import Counter

LABELS = ["CONTRACT_INVALID", "STRUCTURAL_TEST", "NONDISCRIMINATING_ENDPOINT", "DEMONSTRATION",
          "INSUFFICIENT_INFORMATION", "READY_FOR_COMPARISON"]
MUTANTS = {
    "always_ready": lambda c: {"primary": "READY_FOR_COMPARISON", "reason_codes": []},
    "always_insufficient": lambda c: {"primary": "INSUFFICIENT_INFORMATION", "reason_codes": []},
    "always_invalid": lambda c: {"primary": "CONTRACT_INVALID", "reason_codes": []},
    "always_structural": lambda c: {"primary": "STRUCTURAL_TEST", "reason_codes": []},
}


def merge(base, over):
    out = copy.deepcopy(base)
    for k, v in over.items():
        if v is None:
            out.pop(k, None)
        elif isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def load(paths):
    base, cases = None, []
    for p in paths:
        d = json.load(open(p, encoding="utf-8"))
        base = d.get("base_contract", base)
        cases += d["cases"]
    if base is None:
        sys.exit("COULD NOT RUN: no base_contract (pass visible_cases.json first)")
    ids = [c["id"] for c in cases]
    if len(ids) != len(set(ids)) or any(c["expect"] not in LABELS for c in cases):
        sys.exit("COULD NOT RUN: duplicate case ids or unknown expected label")
    return base, cases


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--checker")
    g.add_argument("--mutant", choices=sorted(MUTANTS))
    a = ap.parse_args()
    base, cases = load(a.files)
    if a.mutant:
        classify = MUTANTS[a.mutant]
    else:
        path, fn = a.checker.rsplit(":", 1)
        spec = importlib.util.spec_from_file_location("dpc_checker", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        classify = getattr(mod, fn)
    passed, confusion = 0, Counter()
    for c in cases:
        contract = merge(base, c["overrides"])
        try:
            got = classify(copy.deepcopy(contract))
            prim, codes = got["primary"], list(got.get("reason_codes", []))
        except Exception as e:  # a crash is a failed case, never a skip
            prim, codes = f"CRASH:{type(e).__name__}", []
        need = c.get("reasons_any", [])
        ok = prim == c["expect"] and all(r in codes for r in need)
        passed += ok
        confusion[(c["expect"], prim)] += 1
        print(f"{'PASS' if ok else 'FAIL'}  {c['id']}  expected {c['expect']:<27} got {prim:<27} {'' if ok or not need else 'needs ' + ','.join(need)}")
    print("\nconfusion (expected -> got):")
    for (e, g_), n in sorted(confusion.items()):
        print(f"  {e:<27} -> {g_:<27} {n}")
    print(f"\nVERDICT  {passed} of {len(cases)} cases as expected ({'checker ' + a.checker if a.checker else 'mutant ' + a.mutant})")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    sys.exit(main())
