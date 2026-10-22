"""Offline structure gate for the human-reviewed prior-art register.

This catches *missing/unpinned/contradictory declarations*.
It does NOT verify remote URLs, prove license compliance, or establish novelty.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "research/prior_art_register.json"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
ID = re.compile(r"^PA-[0-9]{3}$")
COMPONENTS = {
    "authorizer", "isolated_execution", "provenance", "eval",
    "origin_experiments", "model_routing", "system_architecture",
}
LICENSE_STATES = {
    "VERIFIED_ROOT_LICENSE", "LICENSE_UNVERIFIED", "NO_ROOT_LICENSE",
    "AUTHOR_DECISION_REQUIRED",
}
KNOWN_LICENSES = {"MIT", "Apache-2.0"}


def require(condition, msg):
    if not condition:
        raise ValueError(msg)


def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def nonempty(x, field):
    require(type(x) is str and len(x.strip()) >= 8, f"{field}: reason missing")
    return x


def check(data):
    require(type(data) is dict and set(data) == {
        "schema_version", "scope", "checked_on", "policy", "records"
    }, "invalid register root fields")
    require(data["schema_version"] == "prior-art-register/v1", "invalid schema")
    require(type(data["scope"]) is str and data["scope"], "scope missing")
    require(type(data["checked_on"]) is str and
            re.fullmatch(r"\d{4}-\d{2}-\d{2}", data["checked_on"]),
            "checked_on date shape invalid")
    nonempty(data["policy"], "reuse policy")
    records = data["records"]
    require(type(records) is list and len(records) >= len(COMPONENTS), "too few prior art records")
    ids = set()
    covered = set()
    for rec in records:
        require(type(rec) is dict and set(rec) == {
            "id", "component", "source_repository", "pinned_revision", "source_url",
            "license", "prior_art_overlap", "unresolved_research_question",
            "proposed_use", "source_code_copied", "attribution_required_in_design",
            "novelty", "review"
        }, "invalid record fields")
        rid = rec["id"]
        require(type(rid) is str and ID.fullmatch(rid), "invalid prior art record ID")
        require(rid not in ids, "duplicate prior art record ID")
        ids.add(rid)
        component = rec["component"]
        require(component in COMPONENTS, "unregistered component category")
        covered.add(component)
        repo, sha, url = rec["source_repository"], rec["pinned_revision"], rec["source_url"]
        require(type(repo) is str and REPO.fullmatch(repo), "bad source repo")
        require(type(sha) is str and HEX40.fullmatch(sha), "source not commit-pinned")
        prefix = f"https://github.com/{repo}/blob/{sha}/"
        require(type(url) is str and url.startswith(prefix) and
                len(url) > len(prefix) and ".." not in url[len(prefix):],
                "source permalink does not match revision")
        lic = rec["license"]
        require(type(lic) is dict and set(lic) == {
            "identifier", "source_url", "status"
        }, "license fields invalid")
        require(lic["status"] in LICENSE_STATES, "license status invalid")
        if lic["status"] == "VERIFIED_ROOT_LICENSE":
            require(lic["identifier"] in KNOWN_LICENSES, "unsupported verified license ID")
            require(lic["source_url"] == prefix + "LICENSE", "verified license URL must be commit-pinned")
        else:
            require(lic["identifier"] in ("NOT_LICENSED", "NOT_CONFIRMED_FOR_REUSE",
                                          "ALL_RIGHTS_RESERVED"),
                    "unsupported unverified/closed license declaration")
            if lic["source_url"] is not None:
                require(lic["source_url"] == prefix + "LICENSE",
                        "unverified license URL mismatched")
        nonempty(rec["prior_art_overlap"], "overlap")
        nonempty(rec["unresolved_research_question"], "research question")
        require(rec["proposed_use"] == "STUDY_ONLY" and
                rec["source_code_copied"] is False,
                "source reuse is not authorized by v1 register")
        require(rec["attribution_required_in_design"] is True,
                "attribution acknowledgement missing")
        require(rec["novelty"] == "NOT_ESTABLISHED",
                "novelty must not be claimed from source review")
        require(rec["review"] == "INITIAL_REVIEW",
                "human clearance has not been recorded")
    require(covered == COMPONENTS, "missing component coverage")
    return {"records": len(records), "components": len(covered),
            "copy_authorizations": 0, "novelty_claims": 0}


def validate(raw):
    data = json.loads(raw, object_pairs_hook=no_duplicates,
                      parse_constant=lambda val: (_ for _ in ()).throw(
                          ValueError("nonfinite JSON: " + val)))
    return check(data)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("path", nargs="?", type=Path, default=DEFAULT)
    args = p.parse_args(argv)
    try:
        result = validate(args.path.read_text(encoding="utf-8"))
    except (ValueError, TypeError, KeyError, OSError) as exc:
        print("PRIOR_ART_GATE: FAIL:", exc, file=sys.stderr)
        return 1
    print("PRIOR_ART_GATE: STRUCTURALLY_CONSISTENT", json.dumps(result, sort_keys=True))
    print("LIMITATIONS: NO REMOTE VALIDATION; NO LICENSE CLEARANCE; NOVELTY NOT ESTABLISHED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
