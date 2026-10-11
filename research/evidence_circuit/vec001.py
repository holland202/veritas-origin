"""VEC-001: experimental, offline, application-scoped DSSE/in-toto binding verifier.

NOT a full in-toto implementation, NOT a scientific truth oracle, and NEVER
an execution authorization mechanism. Frozen DPC-001 v0.2 is untouched.
Dependency: cryptography (Ed25519 verify only; no signing keys in this module).
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

PAYLOAD_TYPE = "application/vnd.in-toto+json"
STATEMENT_TYPE = "https://in-toto.io/Statement/v1"
PREDICATE_TYPE = "https://holland202.github.io/veritas-origin/predicate/evidence-circuit/v0.1"
EVIDENCE_SCHEMA = "vec-evidence-v0.1"
MAX_BYTES = 65536
MAX_PAYLOAD = 32768
MAX_CONTRASTS = 128
MAX_VALUE = 10**12
HEX64 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class TrustedContext:
    study_id: str
    claim_id: str
    contract_sha256: str
    artifact_name: str
    reviewer_role: str
    units: str
    threshold: int
    now_utc: int | None


@dataclass(frozen=True)
class TrustedSigner:
    public_key: Ed25519PublicKey
    role: str


@dataclass(frozen=True)
class Verification:
    binding_status: str
    reason_code: str
    execution_authorized: bool = False
    finite_max_abs_contrast: int | None = None
    finite_set_threshold_reached: bool | None = None


class Rejection(ValueError):
    pass


def _refuse(reason: str) -> Verification:
    return Verification("REFUSED", reason)


def _reject_constant(value: str) -> Any:
    raise Rejection("NONFINITE_JSON")


def _reject_duplicate(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise Rejection("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _json(raw: bytes) -> Any:
    try:
        return json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_reject_duplicate,
            parse_constant=_reject_constant,
        )
    except (ValueError, UnicodeError) as error:
        if isinstance(error, Rejection):
            raise
        raise Rejection("MALFORMED_JSON") from error


def _keys(value: Any, expected: set[str]) -> bool:
    return isinstance(value, dict) and set(value) == expected


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value) and len(value) <= 256


def _strict_int(value: Any, lower: int, upper: int) -> bool:
    return type(value) is int and lower <= value <= upper


def _sha(value: Any) -> bool:
    return isinstance(value, str) and HEX64.fullmatch(value) is not None


def _b64(value: Any) -> bytes:
    if not isinstance(value, str):
        raise Rejection("INVALID_BASE64")
    try:
        return base64.b64decode(value.encode("ascii"), validate=True)
    except (UnicodeError, ValueError, binascii.Error) as error:
        raise Rejection("INVALID_BASE64") from error


def pae(payload_type: str, payload: bytes) -> bytes:
    """DSSE v1 pre-authentication encoding; uses UTF-8 byte lengths."""
    ty = payload_type.encode("utf-8")
    return b"DSSEv1 " + str(len(ty)).encode() + b" " + ty + b" " + str(len(payload)).encode() + b" " + payload


def _validate_context(c: Any) -> bool:
    return (
        isinstance(c, TrustedContext)
        and all(_nonempty(getattr(c, field)) for field in ("study_id", "claim_id", "artifact_name", "reviewer_role", "units"))
        and _sha(c.contract_sha256)
        and _strict_int(c.threshold, 1, MAX_VALUE)
        and _strict_int(c.now_utc, 0, 2**53 - 1)
    )


def verify(
    envelope_bytes: bytes | None,
    artifact_bytes: bytes | None,
    context: TrustedContext,
    trust_map: Mapping[str, TrustedSigner],
) -> Verification:
    """No I/O, no network. Treat all caller-provided bytes as untrusted.

    The trust map and context must be supplied out of band by the host.
    This is *only* an evidence-binding result, never action authorization.
    """
    if not _validate_context(context):
        return _refuse("TRUSTED_CONTEXT_INVALID")
    if not isinstance(artifact_bytes, bytes) or not isinstance(envelope_bytes, bytes):
        return _refuse("MISSING_INPUT")
    if len(artifact_bytes) > MAX_BYTES or len(envelope_bytes) > MAX_BYTES:
        return _refuse("INPUT_TOO_LARGE")
    if not isinstance(trust_map, Mapping) or not trust_map:
        return _refuse("TRUST_ANCHOR_MISSING")

    try:
        env = _json(envelope_bytes)
        if not _keys(env, {"payloadType", "payload", "signatures"}):
            return _refuse("ENVELOPE_SCHEMA_INVALID")
        if env["payloadType"] != PAYLOAD_TYPE:
            return _refuse("PAYLOAD_TYPE_INVALID")
        sigs = env["signatures"]
        if not isinstance(sigs, list) or len(sigs) != 1:
            return _refuse("SIGNATURE_COUNT_INVALID")
        entry = sigs[0]
        if not _keys(entry, {"keyid", "sig"}) or not _nonempty(entry["keyid"]):
            return _refuse("SIGNATURE_SCHEMA_INVALID")
        keyid = entry["keyid"]
        signer = trust_map.get(keyid)
        if not isinstance(signer, TrustedSigner) or not isinstance(signer.public_key, Ed25519PublicKey):
            return _refuse("UNTRUSTED_SIGNER")
        if signer.role != context.reviewer_role:
            return _refuse("SIGNER_ROLE_MISMATCH")
        payload = _b64(env["payload"])
        signature = _b64(entry["sig"])
        if len(payload) > MAX_PAYLOAD:
            return _refuse("PAYLOAD_TOO_LARGE")
        if len(signature) != 64:
            return _refuse("SIGNATURE_INVALID")
        try:
            signer.public_key.verify(signature, pae(env["payloadType"], payload))
        except InvalidSignature:
            return _refuse("SIGNATURE_INVALID")

        # Only parse authenticated payload bytes.
        statement = _json(payload)
        if not _keys(statement, {"_type", "subject", "predicateType", "predicate"}):
            return _refuse("STATEMENT_SCHEMA_INVALID")
        if statement["_type"] != STATEMENT_TYPE or statement["predicateType"] != PREDICATE_TYPE:
            return _refuse("PREDICATE_TYPE_INVALID")
        subjects = statement["subject"]
        if not isinstance(subjects, list) or len(subjects) != 1:
            return _refuse("SUBJECT_COUNT_INVALID")
        sub = subjects[0]
        if not _keys(sub, {"name", "digest"}) or not _keys(sub["digest"], {"sha256"}):
            return _refuse("SUBJECT_SCHEMA_INVALID")
        if sub["name"] != context.artifact_name or not _sha(sub["digest"]["sha256"]):
            return _refuse("SUBJECT_IDENTITY_MISMATCH")
        if sub["digest"]["sha256"] != hashlib.sha256(artifact_bytes).hexdigest():
            return _refuse("ARTIFACT_DIGEST_MISMATCH")

        pred = statement["predicate"]
        if not _keys(pred, {"study_id", "claim_id", "contract_sha256", "reviewer_role", "issued_at", "expires_at"}):
            return _refuse("PREDICATE_SCHEMA_INVALID")
        if (pred["study_id"] != context.study_id or pred["claim_id"] != context.claim_id
                or pred["contract_sha256"] != context.contract_sha256):
            return _refuse("CONTEXT_BINDING_MISMATCH")
        if pred["reviewer_role"] != signer.role:
            return _refuse("REVIEWER_ROLE_MISMATCH")
        if not _strict_int(pred["issued_at"], 0, 2**53 - 1) or not _strict_int(pred["expires_at"], 0, 2**53 - 1):
            return _refuse("PREDICATE_TIME_INVALID")
        if not pred["issued_at"] <= context.now_utc < pred["expires_at"]:
            return _refuse("ATTESTATION_TIME_INVALID")

        evidence = _json(artifact_bytes)
        expected = {"schema", "study_id", "claim_id", "units", "contrasts", "declared_max_abs_contrast"}
        if not _keys(evidence, expected) or evidence["schema"] != EVIDENCE_SCHEMA:
            return _refuse("EVIDENCE_SCHEMA_INVALID")
        if (evidence["study_id"] != context.study_id
                or evidence["claim_id"] != context.claim_id or evidence["units"] != context.units):
            return _refuse("EVIDENCE_CONTEXT_MISMATCH")
        contrasts = evidence["contrasts"]
        if not isinstance(contrasts, list) or not 1 <= len(contrasts) <= MAX_CONTRASTS:
            return _refuse("CONTRAST_SET_INVALID")
        if not all(_strict_int(v, -MAX_VALUE, MAX_VALUE) for v in contrasts):
            return _refuse("CONTRAST_VALUES_INVALID")
        maximum = max(abs(v) for v in contrasts)
        if not _strict_int(evidence["declared_max_abs_contrast"], 0, MAX_VALUE):
            return _refuse("DECLARED_MAX_INVALID")
        if maximum != evidence["declared_max_abs_contrast"]:
            return _refuse("ARITHMETIC_MISMATCH")
        return Verification(
            "BINDING_VERIFIED", "BOUND_FINITE_SET_MATCHES", False,
            maximum, maximum >= context.threshold,
        )
    except Rejection as error:
        return _refuse(str(error))
    except (TypeError, KeyError, ValueError, OverflowError):
        # Invalid caller / hostile decoded input must never become a success.
        return _refuse("INVALID_STRUCTURE")
