"""VEC-001 preregistered self-test fixtures. No production keys; no external I/O.

Execute from the directory containing this script:
    python3 -I test_vec001.py
Exit 0 only if all registered P0/P1/N01–N19 match; failing cases remain visible.
This is author-run development testing, never independent validation.
"""
from __future__ import annotations

import base64
import copy
import hashlib
import json
import platform
import sys
from pathlib import Path

# Explicit trusted local path. Python -I intentionally omits the script directory
# from sys.path; this project loads its own checked-out verifier and no external code.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from vec001 import (
    EVIDENCE_SCHEMA, PAYLOAD_TYPE, PREDICATE_TYPE, STATEMENT_TYPE,
    TrustedContext, TrustedSigner, pae, verify,
)

def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def base_context():
    return TrustedContext(
        study_id="study-a", claim_id="claim-1", contract_sha256="a" * 64,
        artifact_name="evidence.json", reviewer_role="reviewer", units="count",
        threshold=6, now_utc=150,
    )


def evidence_obj():
    return {
        "schema": EVIDENCE_SCHEMA, "study_id": "study-a", "claim_id": "claim-1",
        "units": "count", "contrasts": [2, 5, -1],
        "declared_max_abs_contrast": 5,
    }


def pred_obj():
    return {
        "study_id": "study-a", "claim_id": "claim-1", "contract_sha256": "a" * 64,
        "reviewer_role": "reviewer", "issued_at": 100, "expires_at": 200,
    }


def signed_fixture(private, artifact=None, predicate=None, payload_type=PAYLOAD_TYPE):
    art = encoded(evidence_obj()) if artifact is None else artifact
    statement = {
        "_type": STATEMENT_TYPE,
        "subject": [{"name": "evidence.json", "digest": {"sha256": hashlib.sha256(art).hexdigest()}}],
        "predicateType": PREDICATE_TYPE,
        "predicate": pred_obj() if predicate is None else predicate,
    }
    payload = encoded(statement)
    signature = private.sign(pae(payload_type, payload))
    env = {
        "payloadType": payload_type,
        "payload": base64.b64encode(payload).decode("ascii"),
        "signatures": [{"keyid": "fixture-key", "sig": base64.b64encode(signature).decode("ascii")}],
    }
    return encoded(env), art


def run():
    private = Ed25519PrivateKey.generate()  # ephemeral; no private material written anywhere
    trust = {"fixture-key": TrustedSigner(private.public_key(), "reviewer")}
    ctx = base_context()
    env, art = signed_fixture(private)
    cases = [("P0", env, art, ctx, trust, "BINDING_VERIFIED", "BOUND_FINITE_SET_MATCHES")]

    # P1: signatures authenticate an invented set of numbers, NOT empirical truth.
    fiction = evidence_obj()
    fiction["contrasts"] = [6, 8, -2]
    fiction["declared_max_abs_contrast"] = 8
    env1, art1 = signed_fixture(private, encoded(fiction))
    cases.append(("P1", env1, art1, ctx, trust, "BINDING_VERIFIED", "BOUND_FINITE_SET_MATCHES"))

    cases.append(("N01", env, None, ctx, trust, "REFUSED", "MISSING_INPUT"))
    altered = evidence_obj()
    altered["contrasts"] = [1, 5, -1]  # different bytes but the same maximum
    cases.append(("N02", env, encoded(altered), ctx, trust, "REFUSED", "ARTIFACT_DIGEST_MISMATCH"))

    tampered = json.loads(env)
    payload = base64.b64decode(tampered["payload"])
    assert b'"claim_id":"claim-1"' in payload
    tampered["payload"] = base64.b64encode(payload.replace(b'"claim_id":"claim-1"', b'"claim_id":"claim-2"', 1)).decode("ascii")
    cases.append(("N03", encoded(tampered), art, ctx, trust, "REFUSED", "SIGNATURE_INVALID"))

    wrong_id = json.loads(env)
    wrong_id["signatures"][0]["keyid"] = "not-trusted"
    cases.append(("N04", encoded(wrong_id), art, ctx, trust, "REFUSED", "UNTRUSTED_SIGNER"))
    cases.append(("N05", env, art, ctx, {}, "REFUSED", "TRUST_ANCHOR_MISSING"))

    wrong_type = json.loads(env)
    wrong_type["payloadType"] = "application/x-untrusted"
    cases.append(("N06", encoded(wrong_type), art, ctx, trust, "REFUSED", "PAYLOAD_TYPE_INVALID"))

    from dataclasses import replace
    cases.append(("N07", env, art, replace(ctx, study_id="other-study"), trust, "REFUSED", "CONTEXT_BINDING_MISMATCH"))
    cases.append(("N08", env, art, replace(ctx, claim_id="other-claim"), trust, "REFUSED", "CONTEXT_BINDING_MISMATCH"))
    cases.append(("N09", env, art, replace(ctx, contract_sha256="b" * 64), trust, "REFUSED", "CONTEXT_BINDING_MISMATCH"))
    cases.append(("N10", env, art, replace(ctx, now_utc=200), trust, "REFUSED", "ATTESTATION_TIME_INVALID"))

    extra = evidence_obj()
    extra["status"] = "VALIDATED"
    env11, art11 = signed_fixture(private, encoded(extra))
    cases.append(("N11", env11, art11, ctx, trust, "REFUSED", "EVIDENCE_SCHEMA_INVALID"))

    duplicated = encoded(evidence_obj())
    assert b'"study_id":' in duplicated
    duplicated = duplicated.replace(b'"study_id":', b'"study_id":"study-a","study_id":', 1)
    env12, art12 = signed_fixture(private, duplicated)
    cases.append(("N12", env12, art12, ctx, trust, "REFUSED", "DUPLICATE_JSON_KEY"))

    nonfinite = encoded(evidence_obj()).replace(b'"contrasts":[2,5,-1]', b'"contrasts":[NaN,5,-1]')
    assert b"NaN" in nonfinite
    env13, art13 = signed_fixture(private, nonfinite)
    cases.append(("N13", env13, art13, ctx, trust, "REFUSED", "NONFINITE_JSON"))

    inaccurate = evidence_obj()
    inaccurate["declared_max_abs_contrast"] = 20
    env14, art14 = signed_fixture(private, encoded(inaccurate))
    cases.append(("N14", env14, art14, ctx, trust, "REFUSED", "ARITHMETIC_MISMATCH"))

    wrong_role = pred_obj()
    wrong_role["reviewer_role"] = "operator"
    env15, art15 = signed_fixture(private, predicate=wrong_role)
    cases.append(("N15", env15, art15, ctx, trust, "REFUSED", "REVIEWER_ROLE_MISMATCH"))
    cases.append(("N16", env, art, replace(ctx, now_utc=None), trust, "REFUSED", "TRUSTED_CONTEXT_INVALID"))

    empty = evidence_obj()
    empty["contrasts"] = []
    empty["declared_max_abs_contrast"] = 0
    env17, art17 = signed_fixture(private, encoded(empty))
    cases.append(("N17", env17, art17, ctx, trust, "REFUSED", "CONTRAST_SET_INVALID"))
    cases.append(("N18", env, art, replace(ctx, threshold=0), trust, "REFUSED", "TRUSTED_CONTEXT_INVALID"))

    duplicate_signatures = json.loads(env)
    duplicate_signatures["signatures"].append(copy.deepcopy(duplicate_signatures["signatures"][0]))
    cases.append(("N19", encoded(duplicate_signatures), art, ctx, trust, "REFUSED", "SIGNATURE_COUNT_INVALID"))

    failures = []
    print("VEC-001 SELF-TEST   Python", platform.python_version())
    print("SCOPE: offline fixture signing in memory; no real-world truth or execution authorization")
    for id_, envelope, artifact, context, keys, expected, expected_reason in cases:
        try:
            got = verify(envelope, artifact, context, keys)
            ok = (got.binding_status == expected and got.reason_code == expected_reason
                  and got.execution_authorized is False)
            if id_ == "P0":
                ok = ok and got.finite_max_abs_contrast == 5 and got.finite_set_threshold_reached is False
            if id_ == "P1":
                ok = ok and got.finite_max_abs_contrast == 8 and got.finite_set_threshold_reached is True
            actual = f"{got.binding_status}/{got.reason_code}; execution={got.execution_authorized}"
        except Exception as exc:
            ok = False
            actual = "CRASH " + type(exc).__name__ + ": " + str(exc)
        if not ok:
            failures.append((id_, actual))
        print(f"{id_:<3} {'HELD' if ok else 'REFUTED':<7} {actual}")
    print(f"VERDICT {'PASS' if not failures else 'FAIL'}   matched {len(cases)-len(failures)}/{len(cases)} registered cases")
    if failures:
        print("NEGATIVE FINDINGS:", failures)
    print("LABEL: author-designed local self-test only; NOT independent validation")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(run())
