"""RA-001: read-only historical archive and scoped EXP003-P0 claim assurance.

The frozen pins refer to GitHub main at 2131d9166deea94811155a746e57fb597491f53a.
Git SHA1 blob identities and explicit SHA256 are both checked where available.
This is NOT a sandbox, human-approval oracle, or external scientific validation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

BASELINE_COMMIT = "2131d9166deea94811155a746e57fb597491f53a"
PILOT_PATH = "evidence/pilot-20261008T191115896136Z-e361d9a5.json"
EXP002_PATH = "evidence/exp002/exp002-20261008T194950169959Z-fccc3f26.json"
EXP003_PATH = "evidence/exp003/exp003-p0-20261008T202705724022Z-146bee1a.json"
LEDGER_PATH = "claims/exp003_p0_claims.json"
EXP002_SHA256 = "a5fe362571ea600485cabd6759542314f0e6562e36ea6330feeb06db187faf6c"
EXP003_SHA256 = "627eb778e8eef80d9d664c9ac6f3b7743d51e6a97a677eea8cac51e79b467333"

# Baked-in historical anchors, NOT loaded from a mutable manifest. These may
# only change in a new named preservation protocol, never after an original run.
PINNED = {
    PILOT_PATH: ("8d2d4b0b5bcf060461d9b2f5ac35ce619a568ec5", None),
    EXP002_PATH: ("0ee258670aeeb19ca5bc2ef31a7a79752188a194", EXP002_SHA256),
    EXP003_PATH: ("8b756dccb6c5f686aeadd313ad1e334ebed7255a", EXP003_SHA256),
    "experiments/exp002/PREREG.md":
        ("e4a9d875e3d5df675ccd32e815aad78b3305ab3e", None),
    "experiments/exp003/PROTOCOL_P0.md":
        ("866616cb35e2d820575f20e239ffd58aab92108f", None),
    "experiments/exp003/THREAT_MODEL_P0.md":
        ("a80c6c4b527e7eced30eb7f030059e945ed3168a", None),
    "reports/exp002/EXP002_VERIFICATION.md":
        ("e119bb4806b445c002c4e2e1afbc79f18decb84a", None),
    "reports/exp003/EXP003_P0_AZURE_PILOT.md":
        ("cc11ff055947787cda98edb10066c3ed09d10e45", None),
    "src/origin/exp003.py":
        ("3a614911abe680edc2a98a46cebdfb9156c8e983", None),
    "tools/verify_exp002.py":
        ("248ed3c4db2c122fdee1a4fb157841eedfbccf00", None),
    "tools/verify_exp003_p0.py":
        ("2c751d38c89521c9e0d232dfe9ae42190eea43f6", None),
    LEDGER_PATH:
        ("452c383b1760bae685e8392aca6553b81c29c742", None),
}
EXPECTED_CLAIMS = {
    "EXP003-P0-C01": ("PRESPECIFIED_EXPLORATORY", "DESCRIPTIVE_ONLY",
                       "SUPPORTED_WITHIN_FIXTURE", "tasks_solved"),
    "EXP003-P0-C02": ("POST_HOC_DIAGNOSTIC", "DESCRIPTIVE_ONLY",
                       "SUPPORTED_WITHIN_FIXTURE", "probe_use"),
    "EXP003-P0-C03": ("EXPLORATORY_VERIFICATION", "CONSISTENCY_ONLY",
                       "CONSISTENT_WITH_SPECIFICATION_NOT_WORLD_TRUTH",
                       "internal_replay"),
    "EXP003-P0-C04": ("PILOT_SCOPE", "SCOPE_BOUNDARY",
                       "NO_MODEL_EVALUATED", "external_model_evaluated"),
}
POLICIES = ("fixed", "random", "greedy")
PROBES = {"fixed": 35, "random": 27, "greedy": 24}
SOLVED = {"fixed": 12, "random": 12, "greedy": 12}
EXPECTED_PAIR_COUNT = 36
EXPECTED_TOTAL_PROBES = 86


class AssuranceFailure(ValueError):
    """A failed historical-evidence or claim-accuracy check."""


def demand(condition: bool, reason: str) -> None:
    if not condition:
        raise AssuranceFailure(reason)


def reject_nonfinite(value: str) -> None:
    raise AssuranceFailure("nonfinite JSON numeric value: " + value)


def unique_keys(pairs: list[tuple[str, object]]) -> dict:
    out = {}
    for key, value in pairs:
        demand(key not in out, "duplicate JSON key: " + key)
        out[key] = value
    return out


def strict_json(raw: bytes) -> object:
    demand(type(raw) is bytes and len(raw) <= 8_000_000,
           "evidence is not bounded bytes")
    try:
        return json.loads(raw, object_pairs_hook=unique_keys,
                          parse_constant=reject_nonfinite)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise AssuranceFailure("invalid JSON document") from exc


def git_blob_sha1(raw: bytes) -> str:
    """Git SHA-1 object identity: SHA1('blob '+byte_length+'\\0'+bytes)."""
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()


def protected_bytes(root: Path, filename: str) -> bytes:
    root = Path(root).resolve()
    demand(type(filename) is str and filename in PINNED,
           "unregistered historical path")
    rel = Path(filename)
    demand(not rel.is_absolute() and ".." not in rel.parts, "invalid relative path")
    cur = root
    for part in rel.parts:
        cur = cur / part
        demand(not cur.is_symlink(), "historical artifact symlink refused: " + filename)
    demand(cur.is_file(), "missing historical artifact: " + filename)
    demand(cur.resolve().is_relative_to(root), "historical path escaped checkout")
    size = cur.stat().st_size
    demand(size <= 8_000_000, "historical artifact size unexpectedly large")
    return cur.read_bytes()


def verify_archive(root: Path) -> dict[str, bytes]:
    checked = {}
    for filename, (blob_id, sha256) in PINNED.items():
        raw = protected_bytes(root, filename)
        demand(git_blob_sha1(raw) == blob_id,
               "historical Git blob mismatch: " + filename)
        if sha256 is not None:
            demand(hashlib.sha256(raw).hexdigest() == sha256,
                   "historical SHA256 mismatch: " + filename)
        checked[filename] = raw
    return checked


def rebuild_p0_summary(data: object) -> dict:
    demand(type(data) is dict, "EXP003 evidence not a JSON object")
    demand(data.get("protocol") == "EXP003-P0" and
           data.get("evidence_status") == "EXPLORATORY_SIMULATED",
           "EXP003 pilot misclassified")
    demand(type(data.get("max_steps")) is int and data["max_steps"] == 6,
           "EXP003 maximum probe budget changed")
    demand(data.get("seeds") == list(range(12)) and
           data.get("policies") == list(POLICIES), "EXP003 seed/policy roster changed")
    records = data.get("results")
    demand(type(records) is list and len(records) == EXPECTED_PAIR_COUNT,
           "EXP003 registered inventory incomplete")
    seen = set()
    totals = {p: 0 for p in POLICIES}
    solved = {p: 0 for p in POLICIES}
    for row in records:
        demand(type(row) is dict, "malformed P0 row")
        seed, policy = row.get("seed"), row.get("policy")
        demand(type(seed) is int and seed in range(12) and policy in POLICIES,
               "unknown seed or policy")
        demand((seed, policy) not in seen, "duplicate policy/seed result")
        seen.add((seed, policy))
        entries = row.get("records")
        demand(type(entries) is list and len(entries) <= 6,
               "invalid probe record list")
        demand(type(row.get("solved")) is bool and
               row.get("status") in ("COMPLETE", "DEFERRED"),
               "invalid task completion state")
        totals[policy] += len(entries)
        solved[policy] += int(row["solved"])
    demand(seen == {(s, p) for s in range(12) for p in POLICIES},
           "missing policy/seed result")
    demand(totals == PROBES, "registered probe totals changed")
    demand(solved == SOLVED, "registered completion ceiling changed")
    demand(sum(totals.values()) == EXPECTED_TOTAL_PROBES,
           "registered total probes changed")
    return {
        "solved_by_policy": solved,
        "probes_by_policy": totals,
        "mean_probes_by_policy": {p: totals[p] / 12 for p in POLICIES},
        "policy_task_evaluations": len(records),
        "total_probes": sum(totals.values()),
    }


def compare_numeric(observed, expected, path: str) -> None:
    demand(type(observed) in (int, float) and
           math.isfinite(float(observed)) and
           math.isclose(float(observed), float(expected), rel_tol=1e-13,
                        abs_tol=1e-13), "claim metric mismatch: " + path)


def verify_claim_ledger(ledger: object, counts: dict) -> None:
    demand(type(ledger) is dict and set(ledger) == {
        "schema", "evidence_status", "source_commit",
        "protocol_path", "protocol_classification",
        "evidence_path", "evidence_sha256", "approval_state", "claims",
    }, "claim ledger schema mismatch")
    demand(ledger["schema"] == "veritas-origin.claim-ledger/1" and
           ledger["evidence_status"] == "EXPLORATORY_SIMULATED_NOT_VALIDATED" and
           ledger["source_commit"] == BASELINE_COMMIT,
           "claim ledger baseline revision/status mismatch")
    demand(ledger["protocol_path"] == "experiments/exp003/PROTOCOL_P0.md" and
           ledger["protocol_classification"] == "EXPLORATORY_NOT_CONFIRMATORY",
           "claim protocol was promoted beyond its registered status")
    demand(ledger["evidence_path"] == EXP003_PATH and
           ledger["evidence_sha256"] == EXP003_SHA256,
           "claim ledger evidence is not the original")
    demand(ledger["approval_state"] == "NOT_REQUESTED",
           "claim ledger cannot grant publication authorization")
    claims = ledger["claims"]
    demand(type(claims) is list and len(claims) == len(EXPECTED_CLAIMS),
           "claim inventory changed")
    ids = set()
    for claim in claims:
        demand(type(claim) is dict and
               type(claim.get("id")) is str and
               claim["id"] in EXPECTED_CLAIMS and claim["id"] not in ids,
               "claim id changed or repeated")
        ids.add(claim["id"])
        for key in ("title", "statement", "endpoint", "timing", "inference",
                    "status", "source_paths", "limitations"):
            demand(key in claim, "claim missing required field: " + key)
        demand(type(claim["statement"]) is str and claim["statement"].strip(),
               "claim statement blank")
        demand(type(claim["limitations"]) is list and len(claim["limitations"]) >= 1,
               "claim limitations erased")
        demand(type(claim["source_paths"]) is list and len(claim["source_paths"]) >= 1
               and all(path in PINNED for path in claim["source_paths"]),
               "claim source lineage invalid")
        want = EXPECTED_CLAIMS[claim["id"]]
        demand(tuple(claim[k] for k in ("timing", "inference", "status", "endpoint"))
               == want, "claim improperly promoted or endpoint changed: " + claim["id"])
        if claim["id"] == "EXP003-P0-C01":
            demand(claim["numerator_by_policy"] == counts["solved_by_policy"] and
                   type(claim["denominator_by_policy"]) is int and
                   claim["denominator_by_policy"] == 12,
                   "false completion claim")
        elif claim["id"] == "EXP003-P0-C02":
            demand(claim["total_probes_by_policy"] == counts["probes_by_policy"],
                   "false probe-count claim")
            for policy in POLICIES:
                compare_numeric(claim["mean_probes_by_policy"][policy],
                                counts["mean_probes_by_policy"][policy],
                                "posthoc probes " + policy)
        elif claim["id"] == "EXP003-P0-C03":
            demand(type(claim["policy_task_evaluations"]) is int and
                   claim["policy_task_evaluations"] == counts["policy_task_evaluations"]
                   and type(claim["total_probes"]) is int and
                   claim["total_probes"] == counts["total_probes"],
                   "false historical replay claim")
        elif claim["id"] == "EXP003-P0-C04":
            demand(claim["external_model_evaluated"] is False,
                   "no external model was present")
    demand(ids == set(EXPECTED_CLAIMS), "missing claim IDs")


def audit(root: Path) -> dict:
    original = verify_archive(root)
    evidence = strict_json(original[EXP003_PATH])
    ledger = strict_json(original[LEDGER_PATH])
    counts = rebuild_p0_summary(evidence)
    verify_claim_ledger(ledger, counts)
    return {
        "protocol": "RA-001",
        "baseline_commit": BASELINE_COMMIT,
        "archive_files_pinned": len(PINNED),
        "artifact_integrity": "BYTE_MATCH_TO_PINNED_GIT_OBJECTS",
        "pilot_metric_recalculation": "CONSISTENT_DESCRIPTIVE_COUNTS",
        "pilot_evaluations": counts["policy_task_evaluations"],
        "pilot_probes": counts["total_probes"],
        "claim_ledger": "EXPLORATORY_AND_POSTHOC_DISTINCTIONS_PRESERVED",
        "fresh_reexecution": "NOT_EXECUTED",
        "methodological_validity": "NOT_ESTABLISHED",
        "human_publication_approval": "NOT_GRANTED",
        "verdict": "ARCHIVE_CONSISTENT_ONLY",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    try:
        result = audit(args.root)
    except (AssuranceFailure, ValueError, TypeError, KeyError,
            OSError, OverflowError) as exc:
        print("VERDICT: ARCHIVE_INCONSISTENT_OR_UNVERIFIABLE:", exc, file=sys.stderr)
        return 1
    print("VERDICT: ARCHIVE_CONSISTENT_ONLY")
    print("DETAILS:", json.dumps(result, sort_keys=True))
    print("LIMIT: no independent world truth, methodological approval or publication authorization")
    return 0


if __name__ == "__main__":
    sys.exit(main())
