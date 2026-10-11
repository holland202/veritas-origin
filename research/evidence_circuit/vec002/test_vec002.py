"""VEC-002: adversarial experiments on the unchanged VEC-001 verifier.

Predictions and axes were committed FIRST in vec002/VEC002_PREREG.md.
This script is an author-designed probe, not an independent conformance suite.
Return 1 for a safety failure, even when that failure was predicted.
"""
from __future__ import annotations

import base64
import hashlib
import json
import platform
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from test_vec001 import (
    base_context, encoded, evidence_obj, signed_fixture,
)
from vec001 import (
    PAYLOAD_TYPE, TrustedSigner, Verification, pae, verify,
)


def envelope_with_payload(private, raw_payload: bytes) -> bytes:
    sig = private.sign(pae(PAYLOAD_TYPE, raw_payload))
    return encoded({
        "payloadType": PAYLOAD_TYPE,
        "payload": base64.b64encode(raw_payload).decode("ascii"),
        "signatures": [{
            "keyid": "fixture-key",
            "sig": base64.b64encode(sig).decode("ascii"),
        }],
    })


def deep_json(depth=1500) -> bytes:
    return b"[" * depth + b"0" + b"]" * depth


def make_cases(private, trust, context):
    base_env, base_art = signed_fixture(private)
    out = [("C00", base_env, base_art, context, trust, "BINDING_VERIFIED", "NORMAL")]

    deeply_nested = deep_json()
    assert len(deeply_nested) < 32768
    out.append(("A01", deeply_nested, base_art, context, trust, "CRASH:RecursionError", "INVALID"))
    out.append(("A02", envelope_with_payload(private, deeply_nested), base_art, context, trust,
                "CRASH:RecursionError", "INVALID"))

    signed_bad_art, raw_bad_art = signed_fixture(private, artifact=deeply_nested)
    out.append(("A03", signed_bad_art, raw_bad_art, context, trust, "CRASH:RecursionError", "INVALID"))

    bad_key = json.loads(base_env)
    bad_key["signatures"][0]["keyid"] = "unknown-key"
    out.append(("A04", encoded(bad_key), base_art, context, trust, "REFUSED", "INVALID"))
    out.append(("A05", base_env, base_art, context, {}, "REFUSED", "INVALID"))

    original = json.loads(base_env)
    raw = base64.b64decode(original["payload"])
    token = b'"reviewer_role":"reviewer"'
    assert raw.count(token) == 1
    duplicate_nested = raw.replace(token, b'"reviewer_role":"reviewer","reviewer_role":"reviewer"', 1)
    out.append(("A06", envelope_with_payload(private, duplicate_nested), base_art, context, trust,
                "REFUSED", "INVALID"))

    artifact_nan = encoded(evidence_obj())
    assert b'"contrasts":[2,5,-1]' in artifact_nan
    artifact_nan = artifact_nan.replace(b'"contrasts":[2,5,-1]', b'"contrasts":[NaN,5,-1]')
    nan_env, nan_art = signed_fixture(private, artifact=artifact_nan)
    out.append(("A07", nan_env, nan_art, context, trust, "REFUSED", "INVALID"))

    artifact_inf = encoded(evidence_obj()).replace(b'"contrasts":[2,5,-1]', b'"contrasts":[1e309,5,-1]')
    inf_env, inf_art = signed_fixture(private, artifact=artifact_inf)
    out.append(("A08", inf_env, inf_art, context, trust, "REFUSED", "INVALID"))

    out.append(("A09a", base_env, base_art, context, trust, "BINDING_VERIFIED", "VALID_INDIVIDUALLY"))
    out.append(("A09b", base_env, base_art, context, trust, "BINDING_VERIFIED", "VALID_INDIVIDUALLY"))

    contradict = evidence_obj()
    contradict["contrasts"] = [9, 10]
    contradict["declared_max_abs_contrast"] = 10
    conflicting_env, conflicting_art = signed_fixture(private, artifact=encoded(contradict))
    out.append(("A10a", base_env, base_art, context, trust, "BINDING_VERIFIED", "VALID_INDIVIDUALLY"))
    out.append(("A10b", conflicting_env, conflicting_art, context, trust,
                "BINDING_VERIFIED", "VALID_INDIVIDUALLY"))

    out.append(("A11", base_env, base_art, replace(context, now_utc=201), trust,
                "REFUSED", "INVALID"))
    two_sigs = json.loads(base_env)
    two_sigs["signatures"].append(two_sigs["signatures"][0].copy())
    out.append(("A12", encoded(two_sigs), base_art, context, trust, "REFUSED", "INVALID"))
    return out


def classify_call(envelope, artifact, context, trust):
    try:
        result = verify(envelope, artifact, context, trust)
    except BaseException as exc:
        # A crash is never a security pass. Do not swallow KeyboardInterrupt or SystemExit.
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        return ("CRASH:" + type(exc).__name__, "<NO_TYPED_RESULT>", None, True)
    if not isinstance(result, Verification):
        return ("INVALID_RETURN", "<NO_TYPED_RESULT>", None, True)
    return (result.binding_status, result.reason_code, result.execution_authorized, False)


def main():
    private = Ed25519PrivateKey.generate()
    trust = {"fixture-key": TrustedSigner(private.public_key(), "reviewer")}
    context = base_context()
    rows = make_cases(private, trust, context)

    print("VEC-002 UNMODIFIED TARGET / AUTHOR-DESIGNED ADVERSARIAL EVALUATION")
    print("Python:", platform.python_version(), "architecture:", platform.machine())
    predictions = 0
    safety_failures = []
    prediction_failures = []
    for case_id, envelope, artifact, ctx, keys, predicted, kind in rows:
        observed, reason, authorized, crashed = classify_call(envelope, artifact, ctx, keys)
        matches = observed == predicted
        predictions += int(matches)
        if not matches:
            prediction_failures.append(case_id)
        invariant_ok = not crashed and authorized is False and (
            (kind == "INVALID" and observed == "REFUSED")
            or (kind != "INVALID" and observed == "BINDING_VERIFIED")
        )
        if not invariant_ok:
            safety_failures.append(case_id)
        print(f"{case_id:4}  predicted={predicted:21} observed={observed:21} reason={reason:32} "
              f"size={len(envelope) if isinstance(envelope, bytes) else 'NA'} "
              f"prediction={'MATCH' if matches else 'MISMATCH'} "
              f"typed_contract={'HELD' if invariant_ok else 'FAILED'}")
    print("PREDICTIONS", predictions, "/", len(rows))
    print("S1_TYPED_REFUSAL_FAIL_CASES", ",".join(safety_failures) if safety_failures else "NONE")
    print("PREDICTION_MISMATCH_CASES", ",".join(prediction_failures) if prediction_failures else "NONE")
    print("SCOPE NOTE: A09 and A10 individually verified; no persistent replay/conflict mechanism was tested.")
    print("VERDICT", "FAIL" if safety_failures or prediction_failures else "PASS",
          "(matches to predicted CRASH are always FAIL for the S1 typed-refusal safety invariant)")
    return 1 if safety_failures or prediction_failures else 0


if __name__ == "__main__":
    sys.exit(main())
