#!/usr/bin/env python3
"""MTA-001: read-only, scope-limited claim-to-evidence consistency checker.

Inspired by the *method*, not code, of GuitarPedal's analysis/readme checks.
Exit 0 means typed claims match repository bytes; it does NOT prove science.
Only registered sources are checked; arbitrary report prose is not interpreted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

MAX_SOURCE_BYTES = 2_000_000
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class AuditError(Exception):
    def __init__(self, code: str, claim: str = "registry"):
        self.code = code
        self.claim = claim
        super().__init__(f"{code}: {claim}")


def require_keys(value, exact, code, claim):
    if type(value) is not dict or set(value) != set(exact):
        raise AuditError(code, claim)


def read_json_bytes(raw: bytes, claim: str):
    def pairs_no_dup(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise AuditError("MALFORMED_REGISTRY", claim)
            result[key] = value
        return result

    def no_nonfinite(_):
        raise AuditError("MALFORMED_REGISTRY", claim)

    try:
        return json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=pairs_no_dup,
            parse_constant=no_nonfinite,
        )
    except (ValueError, UnicodeError, RecursionError) as e:
        raise AuditError("MALFORMED_REGISTRY", claim) from e


def source_file(root: Path, relative: str, claim: str) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise AuditError("INVALID_SOURCE_PATH", claim)
    fragment = Path(relative)
    if fragment.is_absolute() or any(part in ("..", ".") for part in relative.split("/")):
        raise AuditError("INVALID_SOURCE_PATH", claim)
    # Reject symlinks escaping the supplied repository root.
    resolved = (root / fragment).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise AuditError("INVALID_SOURCE_PATH", claim)
    if not resolved.is_file():
        raise AuditError("SOURCE_UNAVAILABLE", claim)
    if resolved.stat().st_size > MAX_SOURCE_BYTES:
        raise AuditError("SOURCE_TOO_LARGE", claim)
    return resolved


def source_bytes(root, source, claim):
    path = source_file(root, source, claim)
    try:
        with path.open("rb") as stream:
            raw = stream.read(MAX_SOURCE_BYTES + 1)
    except OSError as e:
        raise AuditError("SOURCE_UNAVAILABLE", claim) from e
    if len(raw) > MAX_SOURCE_BYTES:
        raise AuditError("SOURCE_TOO_LARGE", claim)
    return raw


def audit_case_result(root: Path, item: dict):
    ident = item["id"]
    require_keys(item, ("id", "kind", "source", "expected"), "INVALID_CLAIM", ident)
    expected = item["expected"]
    require_keys(expected, ("total", "passed", "failed", "status", "failed_case_ids"), "INVALID_CLAIM", ident)
    if (any(type(expected[k]) is not int or expected[k] < 0 for k in ("total", "passed", "failed"))
            or expected["total"] <= 0 or expected["status"] not in ("PASS", "FAIL")
            or type(expected["failed_case_ids"]) is not list
            or not all(type(v) is str for v in expected["failed_case_ids"])
            or len(set(expected["failed_case_ids"])) != len(expected["failed_case_ids"])):
        raise AuditError("INVALID_CLAIM", ident)

    observed = read_json_bytes(source_bytes(root, item["source"], ident), ident)
    if type(observed) is not dict or type(observed.get("cases")) is not list or not observed["cases"]:
        raise AuditError("SOURCE_SCHEMA_INVALID", ident)
    case_ids = set()
    failures = []
    passes = 0
    for row in observed["cases"]:
        if type(row) is not dict or any(k not in row for k in (
                "case_id", "expected_primary", "actual_primary", "issues", "status")):
            raise AuditError("SOURCE_SCHEMA_INVALID", ident)
        cid = row["case_id"]
        if (type(cid) is not str or not cid or cid in case_ids
                or type(row["expected_primary"]) is not str
                or type(row["actual_primary"]) is not str
                or type(row["issues"]) is not list
                or not all(type(x) is str for x in row["issues"])):
            raise AuditError("SOURCE_SCHEMA_INVALID", ident)
        case_ids.add(cid)
        row_consistent = row["expected_primary"] == row["actual_primary"] and not row["issues"]
        if row_consistent and row["status"] == "PASS":
            passes += 1
        elif not row_consistent and row["status"] == "FAIL":
            failures.append(cid)
        else:
            raise AuditError("CASE_ROW_CONTRADICTION", ident + ":" + cid)
    derived_status = "PASS" if not failures else "FAIL"
    if observed.get("status") != derived_status:
        raise AuditError("RESULT_SUMMARY_DRIFT", ident)
    derived = {
        "total": len(case_ids),
        "passed": passes,
        "failed": len(failures),
        "status": derived_status,
        "failed_case_ids": sorted(failures),
    }
    pinned = dict(expected)
    pinned["failed_case_ids"] = sorted(expected["failed_case_ids"])
    if pinned != derived:
        raise AuditError("CLAIM_DRIFT", ident)
    return "MACHINE_CHECKED"


def audit_byte_digest(root: Path, item: dict):
    ident = item["id"]
    require_keys(item, ("id", "kind", "sources"), "INVALID_CLAIM", ident)
    entries = item["sources"]
    if type(entries) is not list or not entries:
        raise AuditError("INVALID_CLAIM", ident)
    paths = set()
    for entry in entries:
        require_keys(entry, ("path", "sha256"), "INVALID_CLAIM", ident)
        path, digest = entry["path"], entry["sha256"]
        if (type(path) is not str or path in paths or type(digest) is not str
                or HEX64.fullmatch(digest) is None):
            raise AuditError("INVALID_CLAIM", ident)
        paths.add(path)
        raw = source_bytes(root, path, ident)
        if hashlib.sha256(raw).hexdigest() != digest:
            raise AuditError("SOURCE_DIGEST_DRIFT", ident + ":" + path)
    return "MACHINE_CHECKED"


def audit_reported_only(root: Path, item: dict):
    ident = item["id"]
    require_keys(item, (
        "id", "kind", "source", "status", "reported",
        "independent_verification", "raw_evidence_present",
    ), "INVALID_CLAIM", ident)
    require_keys(item["reported"], ("total", "passed", "status"), "INVALID_CLAIM", ident)
    if (item["status"] != "OWNER_REPORTED"
            or item["independent_verification"] is not False
            or item["raw_evidence_present"] is not False):
        raise AuditError("PROVENANCE_PROMOTION", ident)
    report = item["reported"]
    if (type(report["total"]) is not int or report["total"] < 1
            or type(report["passed"]) is not int or not 0 <= report["passed"] <= report["total"]
            or report["status"] not in ("PASS", "FAIL")):
        raise AuditError("INVALID_CLAIM", ident)
    # Source is read only for existence and boundedness; its prose and any
    # sealed evidence are NOT independently checked here.
    source_bytes(root, item["source"], ident)
    return "DISCLOSED_ONLY"


def audit(root: Path, registry_file: Path):
    raw = registry_file.read_bytes()
    if len(raw) > MAX_SOURCE_BYTES:
        raise AuditError("SOURCE_TOO_LARGE")
    registry = read_json_bytes(raw, "registry")
    require_keys(registry, ("schema", "claims"), "MALFORMED_REGISTRY", "registry")
    if registry["schema"] != "mta-claims-v1" or type(registry["claims"]) is not list or not registry["claims"]:
        raise AuditError("MALFORMED_REGISTRY")
    handlers = {
        "case_result": audit_case_result,
        "byte_digest": audit_byte_digest,
        "reported_only": audit_reported_only,
    }
    seen = set()
    checked = disclosed = 0
    for item in registry["claims"]:
        if type(item) is not dict or type(item.get("id")) is not str or not item["id"]:
            raise AuditError("INVALID_CLAIM")
        ident = item["id"]
        if ident in seen:
            raise AuditError("INVALID_CLAIM", ident)
        seen.add(ident)
        handler = handlers.get(item.get("kind"))
        if handler is None:
            raise AuditError("INVALID_CLAIM", ident)
        verdict = handler(root, item)
        checked += verdict == "MACHINE_CHECKED"
        disclosed += verdict == "DISCLOSED_ONLY"
        print(ident, verdict)
    if not checked or not disclosed:
        # Fail closed if someone silently drops all hard checks or the open
        # provenance boundary. A new version must revise this instrument.
        raise AuditError("INVALID_CLAIM", "anti_vacuity")
    print("OVERALL CONSISTENT_WITH_UNVERIFIED", f"machine_checked={checked}", f"disclosed_only={disclosed}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        return audit(args.root.resolve(), args.registry)
    except AuditError as e:
        print("AUDIT_FAIL", e.code, e.claim)
        return 2
    except (OSError, ValueError, RecursionError, TypeError) as e:
        print("AUDIT_FAIL", "INSTRUMENT_ERROR", type(e).__name__)
        return 2


if __name__ == "__main__":
    sys.exit(main())
