"""VEC-003-S1: 900 hostile/positive repeated verifications in isolated process.

Preregistration VEC003_S1_PREREG.md committed before this file; this suite is
not independent security validation and doesn't replace VEC003 original tests.
"""
from __future__ import annotations

import base64
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def child() -> int:
    # Explicit external process limits. The verifier does NOT impose hard
    # memory/CPU limits on its own when embedded without this host isolation.
    import resource
    memory = 256 * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (memory, memory))
    resource.setrlimit(resource.RLIMIT_CPU, (8, 8))
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "vec002"))

    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from test_vec001 import base_context, encoded, evidence_obj, signed_fixture
    from test_vec002 import envelope_with_payload
    from vec001 import TrustedSigner, Verification, verify

    secret = Ed25519PrivateKey.generate()
    ctx = base_context()
    trust = {"fixture-key": TrustedSigner(secret.public_key(), "reviewer")}
    env, art = signed_fixture(secret)
    deep = b"[" * 1500 + b"0" + b"]" * 1500
    signed_deep, deep_art = signed_fixture(secret, artifact=deep)
    commas = b"[" + b"0," * 4097 + b"0]"
    signed_wide, wide_art = signed_fixture(secret, artifact=commas)
    padded_env = env + b" " * (65537 - len(env))
    payload = base64.b64decode(json.loads(env)["payload"])
    signed_payload = envelope_with_payload(secret, payload + b" " * (32769 - len(payload)))
    large_num = encoded(evidence_obj()).replace(
        b'"contrasts":[2,5,-1]', b'"contrasts":[' + b"1" * 6000 + b",5,-1]"
    )
    if b"1" * 6000 not in large_num:
        print("S1_FIXTURE_FAILURE failed to build decimal number")
        return 1
    large_num_env, large_num_art = signed_fixture(secret, artifact=large_num)
    signed_max_art, max_art = signed_fixture(secret, artifact=art + b" " * (65536 - len(art)))

    cases = [
        ("H00", env, art, "BINDING_VERIFIED", "BOUND_FINITE_SET_MATCHES"),
        ("H01", deep, art, "REFUSED", "MALFORMED_JSON"),
        ("H02", envelope_with_payload(secret, deep), art, "REFUSED", "MALFORMED_JSON"),
        ("H03", signed_deep, deep_art, "REFUSED", "MALFORMED_JSON"),
        ("H04", signed_wide, wide_art, "REFUSED", "MALFORMED_JSON"),
        ("H05", padded_env, art, "REFUSED", "INPUT_TOO_LARGE"),
        ("H06", signed_payload, art, "REFUSED", "PAYLOAD_TOO_LARGE"),
        ("H07", large_num_env, large_num_art, "REFUSED", "MALFORMED_JSON"),
        ("H08", signed_max_art, max_art, "BINDING_VERIFIED", "BOUND_FINITE_SET_MATCHES"),
    ]
    begin = time.monotonic()
    total = 0
    for ident, envelope, artifact, expected_status, expected_reason in cases:
        for iteration in range(100):
            try:
                got = verify(envelope, artifact, ctx, trust)
            except Exception as exc:
                print("S1_FAIL", ident, iteration, "CRASH:", type(exc).__name__)
                return 1
            if (not isinstance(got, Verification)
                    or got.binding_status != expected_status
                    or got.reason_code != expected_reason
                    or got.execution_authorized is not False):
                print("S1_FAIL", ident, iteration, "EXPECTED",
                      expected_status, expected_reason, "OBSERVED", got)
                return 1
            total += 1
        print("S1_CLASS_PASS", ident, "100/100")
    elapsed = (time.monotonic() - begin) * 1000
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print("VEC003_S1_PASS", f"{total}/900",
          "python=" + platform.python_version(),
          "elapsed_inner_ms=" + format(elapsed, ".2f"),
          "peak_rss_kib=" + str(peak),
          "rlimit_as_mib=256", "rlimit_cpu_s=8")
    return 0 if total == 900 else 1


def parent() -> int:
    try:
        r = subprocess.run(
            [sys.executable, "-I", str(Path(__file__).resolve()), "--child"],
            cwd=HERE, text=True, capture_output=True, check=False, timeout=15,
        )
    except subprocess.TimeoutExpired:
        print("VEC003_S1_FAIL timeout 15s")
        return 1
    print("VEC003_S1_CHILD_EXIT", r.returncode)
    if r.stdout:
        print(r.stdout.rstrip())
    if r.stderr.strip():
        print("VEC003_S1_CHILD_STDERR", r.stderr[-800:])
    if r.returncode != 0 or "VEC003_S1_PASS 900/900" not in r.stdout:
        print("VEC003_S1_VERDICT FAIL")
        return 1
    print("VEC003_S1_VERDICT PASS — visible author-designed stress matrix only")
    return 0


if __name__ == "__main__":
    sys.exit(child() if "--child" in sys.argv else parent())
