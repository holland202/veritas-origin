"""Read-only Sovereign Veritas sv.gate/0 input adapter for research claims.

This emits an UNAUTHORIZED review intent. It does not call an external
publisher, mint a capability, certify methodology, or execute an AI agent.
The real SV Gate from its MIT-licensed pinned repository is tested separately.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_assurance():
    path = ROOT / "tools/research_assurance.py"
    spec = importlib.util.spec_from_file_location("origin_research_assurance", path)
    assert spec and spec.loader
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


ASSURANCE = load_assurance()
ACTION = "publish_research_claim"
EVIDENCE_FIELDS = (
    "archive_integrity",
    "independent_replay",
    "methodology_reviewed",
    "human_approval_verified",
    "baseline_sources_pinned",
)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def bridge_intent(root: Path, claim_id: str):
    """Output is ALWAYS unauthorized, even when original evidence matches.

    User-controlled strings/JSON can never enable this action. An external
    verified, scoped human-approval system would be a separate implementation.
    """
    assurance = ASSURANCE.audit(root)
    raw = ASSURANCE.protected_bytes(root, ASSURANCE.LEDGER_PATH)
    ledger = ASSURANCE.strict_json(raw)
    matches = [c for c in ledger["claims"] if c["id"] == claim_id]
    ASSURANCE.demand(len(matches) == 1, "claim id missing from frozen ledger")
    claim = matches[0]
    digest = hashlib.sha256(canonical({
        "claim": claim, "evidence_sha256": ASSURANCE.EXP003_SHA256,
        "source_commit": ASSURANCE.BASELINE_COMMIT,
        "requested_action": ACTION,
    })).hexdigest()
    # Protocol scoped science is not independently valid just because the
    # archived mechanics and descriptive measurements replay.
    return {
        "record": {
            "input_digest": digest,
            "verification": {"status": "INSUFFICIENT_EVIDENCE"},
            "action": {"requested": ACTION, "capability": ACTION},
            "metadata": {
                "archive_integrity":
                    assurance["artifact_integrity"] == "BYTE_MATCH_TO_PINNED_GIT_OBJECTS",
                "independent_replay": False,  # separate original verifier not called here
                "methodology_reviewed": False,
                "human_approval_verified": False,
                "baseline_sources_pinned": True,
                "research_status": "EXPLORATORY_SIMULATED_NOT_VALIDATED",
                "claim_id": claim_id,
                "source_commit": ASSURANCE.BASELINE_COMMIT,
                "evidence_sha256": ASSURANCE.EXP003_SHA256,
            },
            "evidence_quality": None,
        },
        "capability": {
            "name": ACTION,
            "authorized": False,  # No human authority is created by this adapter.
            "required_evidence": list(EVIDENCE_FIELDS),
            "parent": None,
            "min_evidence_quality": None,
            "max_steps": None,
        },
        "capability_registry": None,
        "runtime": {
            # Never default unknown operating conditions to healthy values.
            "thermal_status": "unknown",
            "compute_budget": "unknown",
            "power_status": "unknown",
        },
        "policy": {"allow_only": [ACTION]},
    }


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--claim-id",required=True)
    args=p.parse_args(argv)
    try:
        packet=bridge_intent(args.root,args.claim_id)
    except (ASSURANCE.AssuranceFailure, ValueError, TypeError, KeyError, OSError) as exc:
        print("HALT: UNVERIFIABLE_REVIEW_INTENT:",exc,file=sys.stderr)
        return 1
    print(json.dumps(packet,sort_keys=True,allow_nan=False))
    print("STATUS: UNAUTHORIZED_REVIEW_INTENT_ONLY — PUBLICATION NOT ALLOWED",
          file=sys.stderr)
    return 0


if __name__=="__main__":
    sys.exit(main())
