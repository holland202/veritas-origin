#!/usr/bin/env python3
"""MTA-001 visible, preregistered anti-vacuity/mutation test matrix.

Uses copies of the actual repository evidence in temporary directories.
The executed auditor is the same audit_claims.py file checked into this repo.
This is self-testing, not an independent scientific review.
"""
from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
AUDITOR = HERE / "audit_claims.py"
REGISTRY = HERE / "CLAIMS.json"
BLIND1 = "coordination/dpc001_v02/blind_run_1/evidence/blind_run_v1.json"
CHECKER = "coordination/dpc001_v02/checker.py"


def fixture(root: Path):
    doc = json.loads(REGISTRY.read_text())
    sources = [BLIND1, CHECKER, "coordination/dpc001_v02/SPEC_V02_DRAFT.md",
               "coordination/dpc001_v02/blind_run_2/RECORD.md"]
    for source in sources:
        dest = root / source
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / source, dest)
    target = root / "CLAIMS.json"
    target.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return doc, target


def json_edit(root, path, modifier):
    p = root / path
    obj = json.loads(p.read_text())
    modifier(obj)
    p.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def change(root, case, registry):
    if case == "N01":
        json_edit(root, BLIND1, lambda d: d["cases"][1].__setitem__("actual_primary", "READY_FOR_COMPARISON"))
    elif case == "N02":
        json_edit(root, BLIND1, lambda d: d["cases"][0].__setitem__("status", "PASS"))
    elif case == "N03":
        json_edit(root, BLIND1, lambda d: d.__setitem__("status", "PASS"))
    elif case == "N04":
        json_edit(root, "CLAIMS.json", lambda d: d["claims"][0]["expected"].__setitem__("passed", 24))
    elif case == "N05":
        with (root / CHECKER).open("ab") as f:
            f.write(b"\n# tampered fixture\n")
    elif case == "N06":
        json_edit(root, "CLAIMS.json", lambda d: d["claims"][2].__setitem__("independent_verification", True))
    elif case == "N07":
        json_edit(root, "CLAIMS.json", lambda d: d["claims"][2].__setitem__("raw_evidence_present", True))
    elif case == "N08":
        registry.write_text(
            registry.read_text().replace(
                '"schema": "mta-claims-v1",', '"schema": "mta-claims-v1", "schema": "mta-claims-v1",', 1
            ), encoding="utf-8"
        )
    elif case == "N09":
        json_edit(root, "CLAIMS.json", lambda d: d["claims"][0].__setitem__("source", "../outside.json"))
    elif case == "N10":
        json_edit(root, "CLAIMS.json", lambda d: d["claims"][0]["expected"].__setitem__("total", 0))


EXPECTED = {
    "B00": ("CONSISTENT_WITH_UNVERIFIED", 0),
    "N01": ("CASE_ROW_CONTRADICTION", 2),
    "N02": ("CASE_ROW_CONTRADICTION", 2),
    "N03": ("RESULT_SUMMARY_DRIFT", 2),
    "N04": ("CLAIM_DRIFT", 2),
    "N05": ("SOURCE_DIGEST_DRIFT", 2),
    "N06": ("PROVENANCE_PROMOTION", 2),
    "N07": ("PROVENANCE_PROMOTION", 2),
    "N08": ("MALFORMED_REGISTRY", 2),
    "N09": ("INVALID_SOURCE_PATH", 2),
    "N10": ("INVALID_CLAIM", 2),
}


def main():
    failed = []
    for case, (marker, rc) in EXPECTED.items():
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _, registry = fixture(root)
            change(root, case, registry)
            result = subprocess.run(
                [sys.executable, "-I", str(AUDITOR), "--root", str(root),
                 "--registry", str(registry)],
                capture_output=True, text=True, check=False, timeout=15,
            )
            good = result.returncode == rc and marker in result.stdout
            if case == "B00":
                good = good and "machine_checked=2" in result.stdout and "disclosed_only=1" in result.stdout
            if not good:
                failed.append(case)
            print(f"{case} {'HELD' if good else 'FAIL'} exit={result.returncode} "
                  f"expected_exit={rc} expected_marker={marker}")
            if not good:
                print("ACTUAL_STDOUT", result.stdout[-900:])
                print("ACTUAL_STDERR", result.stderr[-900:])
    print(f"MTA001 VERDICT {'PASS' if not failed else 'FAIL'} "
          f"{len(EXPECTED)-len(failed)}/{len(EXPECTED)}")
    print("FAILED_CASES", ",".join(failed) if failed else "NONE")
    print("SELF-TEST ONLY: matching the original committed evidence is not independent scientific validation")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
