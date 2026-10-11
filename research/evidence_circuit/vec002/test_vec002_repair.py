"""VEC-002-R1: post-finding repair matrix, prospectively registered before patch.

This test expects A01-A03 to return REFUSED/MALFORMED_JSON on the
patched candidate. It must NOT replace or edit VEC-002's original
registered predictions (CRASH), original FAIL workflow or findings.
"""
from __future__ import annotations

import platform
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from test_vec002 import make_cases, classify_call
from vec001 import TrustedSigner

REASONS = {
    "C00": ("BINDING_VERIFIED", "BOUND_FINITE_SET_MATCHES"),
    "A01": ("REFUSED", "MALFORMED_JSON"),
    "A02": ("REFUSED", "MALFORMED_JSON"),
    "A03": ("REFUSED", "MALFORMED_JSON"),
    "A04": ("REFUSED", "UNTRUSTED_SIGNER"),
    "A05": ("REFUSED", "TRUST_ANCHOR_MISSING"),
    "A06": ("REFUSED", "DUPLICATE_JSON_KEY"),
    "A07": ("REFUSED", "NONFINITE_JSON"),
    "A08": ("REFUSED", "CONTRAST_VALUES_INVALID"),
    "A09a": ("BINDING_VERIFIED", "BOUND_FINITE_SET_MATCHES"),
    "A09b": ("BINDING_VERIFIED", "BOUND_FINITE_SET_MATCHES"),
    "A10a": ("BINDING_VERIFIED", "BOUND_FINITE_SET_MATCHES"),
    "A10b": ("BINDING_VERIFIED", "BOUND_FINITE_SET_MATCHES"),
    "A11": ("REFUSED", "ATTESTATION_TIME_INVALID"),
    "A12": ("REFUSED", "SIGNATURE_COUNT_INVALID"),
}


def run():
    # No private key is persisted. All remote action permissions remain absent.
    from test_vec001 import base_context
    key = Ed25519PrivateKey.generate()
    trust = {"fixture-key": TrustedSigner(key.public_key(), "reviewer")}
    cases = make_cases(key, trust, base_context())
    failures = []
    print("VEC-002-R1 POST-FINDING REPAIR / LOCAL AUTHOR-DESIGNED MATRIX")
    print("PYTHON", platform.python_version(), platform.machine())
    for case_id, envelope, artifact, context, trust_map, old_expected, kind in cases:
        actual, reason, authorized, crashed = classify_call(envelope, artifact, context, trust_map)
        expected, expected_reason = REASONS[case_id]
        ok = (actual == expected and reason == expected_reason and
              not crashed and authorized is False)
        if case_id in ("A01", "A02", "A03"):
            ok = ok and len(envelope) < 65536 and len(artifact) < 65536
        if not ok:
            failures.append(case_id)
        print(f"{case_id:4} {'HELD' if ok else 'FAILED':<6} "
              f"expected={expected}/{expected_reason} "
              f"actual={actual}/{reason} execution={authorized}")
    print("VERDICT", "FAIL" if failures else "PASS",
          f"matching={len(cases)-len(failures)}/{len(cases)}")
    print("FAIL_CASES", ",".join(failures) if failures else "NONE")
    print("ORIGINAL VEC-002 CRASH PREDICTIONS PRESERVED — THIS IS A NEW REPAIR STUDY")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(run())
