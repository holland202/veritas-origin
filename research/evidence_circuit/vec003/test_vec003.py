"""VEC-003: prospectively registered parser budget boundary matrix.

Not independent. Uses ephemeral keys, no production data. Verifier under test
is the separate VEC-003 branch; original VEC-001/VEC-002 evidence is immutable.
"""
from __future__ import annotations

import base64
import json
import platform
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from test_vec001 import base_context, encoded, evidence_obj, signed_fixture
from test_vec002 import envelope_with_payload
from vec001 import (
    MAX_BYTES, MAX_PAYLOAD, MAX_JSON_DEPTH, MAX_JSON_PUNCTUATION,
    TrustedSigner, Verification, verify,
)


def deep(depth):
    return b"[" * depth + b"0" + b"]" * depth


def signed_art(private, artifact):
    return signed_fixture(private, artifact=artifact)


def build(private, trust, ctx):
    env, art = signed_fixture(private)
    passed = "BINDING_VERIFIED", "BOUND_FINITE_SET_MATCHES"
    malformed = "REFUSED", "MALFORMED_JSON"
    rows = [("P00", env, art, ctx, trust, *passed)]
    rows.extend([
        ("D01", deep(MAX_JSON_DEPTH), art, ctx, trust, "REFUSED", "ENVELOPE_SCHEMA_INVALID"),
        ("D02", deep(MAX_JSON_DEPTH + 1), art, ctx, trust, *malformed),
        ("D03", envelope_with_payload(private, deep(MAX_JSON_DEPTH)), art, ctx, trust,
         "REFUSED", "STATEMENT_SCHEMA_INVALID"),
        ("D04", envelope_with_payload(private, deep(MAX_JSON_DEPTH + 1)), art, ctx, trust, *malformed),
    ])
    env64, art64 = signed_art(private, deep(MAX_JSON_DEPTH))
    env65, art65 = signed_art(private, deep(MAX_JSON_DEPTH + 1))
    rows.extend([
        ("D05", env64, art64, ctx, trust, "REFUSED", "EVIDENCE_SCHEMA_INVALID"),
        ("D06", env65, art65, ctx, trust, *malformed),
    ])

    for case_id, units in (
        ("D07", "[" * 75 + "{" * 75),
        ("D08", "\\\"" + "[" * 75 + "}" * 75),  # escaped quote/backslash inside JSON
    ):
        assert len(units) <= 256
        modified = evidence_obj()
        modified["units"] = units
        new_env, new_art = signed_art(private, encoded(modified))
        rows.append((case_id, new_env, new_art, replace(ctx, units=units), trust, *passed))

    large = deep(1500)
    huge_env, huge_art = signed_art(private, large)
    rows.extend([
        ("D09a", large, art, ctx, trust, *malformed),
        ("D09b", envelope_with_payload(private, large), art, ctx, trust, *malformed),
        ("D09c", huge_env, huge_art, ctx, trust, *malformed),
    ])

    assert len(env) < MAX_BYTES and len(art) < MAX_BYTES
    envelope_at_cap = env + b" " * (MAX_BYTES - len(env))
    rows.extend([
        ("R01", envelope_at_cap, art, ctx, trust, *passed),
        ("R02", envelope_at_cap + b" ", art, ctx, trust, "REFUSED", "INPUT_TOO_LARGE"),
    ])

    artifact_at_cap = art + b" " * (MAX_BYTES - len(art))
    art_env, _ = signed_art(private, artifact_at_cap)
    rows.extend([
        ("R03", art_env, artifact_at_cap, ctx, trust, *passed),
        ("R04", art_env, artifact_at_cap + b" ", ctx, trust, "REFUSED", "INPUT_TOO_LARGE"),
    ])

    template = json.loads(env)
    payload = base64.b64decode(template["payload"])
    assert len(payload) < MAX_PAYLOAD
    rows.extend([
        ("R05", envelope_with_payload(private, payload + b" " * (MAX_PAYLOAD-len(payload))),
         art, ctx, trust, *passed),
        ("R06", envelope_with_payload(private, payload + b" " * (MAX_PAYLOAD+1-len(payload))),
         art, ctx, trust, "REFUSED", "PAYLOAD_TOO_LARGE"),
    ])

    wide_high = b"[" + b"0," * (MAX_JSON_PUNCTUATION + 1) + b"0]"
    wide_edge = b"[" + b"0," * MAX_JSON_PUNCTUATION + b"0]"
    assert wide_high.count(b",") == MAX_JSON_PUNCTUATION + 1
    assert wide_edge.count(b",") == MAX_JSON_PUNCTUATION
    high_env, _ = signed_art(private, wide_high)
    edge_env, _ = signed_art(private, wide_edge)
    rows.extend([
        ("R07", high_env, wide_high, ctx, trust, *malformed),
        ("R08", edge_env, wide_edge, ctx, trust, "REFUSED", "EVIDENCE_SCHEMA_INVALID"),
    ])
    long_number = encoded(evidence_obj()).replace(
        b'"contrasts":[2,5,-1]', b'"contrasts":[' + b"1" * 6000 + b",5,-1]"
    )
    assert b"1" * 6000 in long_number
    integer_env, _ = signed_art(private, long_number)
    rows.append(("R09", integer_env, long_number, ctx, trust, *malformed))
    return rows


def run():
    private = Ed25519PrivateKey.generate()
    trust = {"fixture-key": TrustedSigner(private.public_key(), "reviewer")}
    rows = build(private, trust, base_context())
    failures = []
    print("VEC-003 DEPTH + PUNCTUATION + SIZE BOUNDARY TESTS")
    print("Python", platform.python_version(), platform.machine(), "depth", MAX_JSON_DEPTH,
          "punctuation", MAX_JSON_PUNCTUATION)
    for case_id, envelope, artifact, ctx, trust_map, status, reason in rows:
        try:
            got = verify(envelope, artifact, ctx, trust_map)
            ok = (
                isinstance(got, Verification)
                and got.binding_status == status and got.reason_code == reason
                and got.execution_authorized is False
            )
            actual = f"{got.binding_status}/{got.reason_code} execution={got.execution_authorized}"
        except Exception as error:
            actual, ok = "CRASH:" + type(error).__name__, False
        if not ok:
            failures.append(case_id)
        print(f"{case_id:4} {'HELD' if ok else 'FAIL':<4} expected={status}/{reason} actual={actual}"
              f" bytes=({len(envelope)},{len(artifact)})")

    command = [sys.executable, "-I", "test_vec003_resource_child.py"]
    try:
        proc = subprocess.run(
            command, cwd=Path(__file__).resolve().parent, capture_output=True,
            text=True, timeout=15, check=False,
        )
        child_ok = proc.returncode == 0 and "R10_CHILD PASS 100/100" in proc.stdout
        print("R10_CHILD_EXIT", proc.returncode)
        print(proc.stdout.strip())
        if proc.stderr.strip():
            print("R10_CHILD_STDERR", proc.stderr.strip()[-600:])
    except subprocess.TimeoutExpired:
        child_ok = False
        print("R10_CHILD_TIMEOUT 15sec")
    if not child_ok:
        failures.append("R10")
    print("VERDICT", "PASS" if not failures else "FAIL",
          f"{len(rows)+int(child_ok)-len(failures)+(0 if child_ok else 1)}/{len(rows)+1}")
    print("FAIL_CASES", ",".join(failures) if failures else "NONE")
    print("AUTHOR-DESIGNED VISIBLE CASES; no independent security certification")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(run())
