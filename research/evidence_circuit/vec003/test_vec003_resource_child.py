"""VEC-003 R10 isolated Linux child: 100 valid signed verifications.

Process limits are an *outer* host safety boundary, not guarantees by vec001.
Run only through the VEC-003 parent watchdog (15 seconds).
"""
from __future__ import annotations

import platform
import resource
import sys
import time
from pathlib import Path

BYTES_256_MIB = 256 * 1024 * 1024
resource.setrlimit(resource.RLIMIT_AS, (BYTES_256_MIB, BYTES_256_MIB))
resource.setrlimit(resource.RLIMIT_CPU, (8, 8))

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from test_vec001 import base_context, signed_fixture
from vec001 import TrustedSigner, verify


def run():
    key = Ed25519PrivateKey.generate()
    trust = {"fixture-key": TrustedSigner(key.public_key(), "reviewer")}
    context = base_context()
    env, artifact = signed_fixture(key)
    start = time.monotonic()
    for attempt in range(100):
        result = verify(env, artifact, context, trust)
        if (result.binding_status != "BINDING_VERIFIED"
                or result.reason_code != "BOUND_FINITE_SET_MATCHES"
                or result.execution_authorized is not False):
            print("R10_CHILD FAIL at", attempt, result)
            return 1
    elapsed_ms = (time.monotonic() - start) * 1000
    peak_kib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print("R10_CHILD PASS 100/100", "python="+platform.python_version(),
          "wall_ms="+format(elapsed_ms, ".3f"),
          "peak_rss_kib="+str(peak_kib),
          "rlimit_as_mib=256 rlimit_cpu_s=8")
    return 0


if __name__ == "__main__":
    sys.exit(run())
