"""EXP003-P1 offline proposal exchange: strict message admission, not sandboxing.

No model is executed here. This module cannot enforce filesystem/network/OS
isolation, authenticate a producer, atomically reserve a request or authorize
an experiment. All effects remain the trusted evaluator's responsibility.
"""
import hashlib
import json
import secrets

SCHEMA = "EXP003-P1-OFFLINE-REQUEST/v1"
HYPOTHESES = tuple(f"H{i:02d}" for i in range(16))
PROBES = tuple(range(24))
REQUEST_KEYS = {"protocol", "request_id", "expires_at_unix",
                "hypotheses", "candidate_names", "matrix",
                "available_probes", "observations", "remaining_budget"}
RESPONSE_KEYS = {"request_id", "request_sha256", "probe"}


class ProposalRejected(ValueError):
    """Non-authorizing reject; reason suitable for a structured failure record."""


def _require(test, reason):
    if not test:
        raise ProposalRejected(reason)


def _strict_object(pairs):
    out = {}
    for key, value in pairs:
        _require(key not in out, "DUPLICATE_JSON_KEY")
        out[key] = value
    return out


def _bad_constant(value):
    raise ProposalRejected("NONFINITE_JSON")


def canonical_bytes(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=True,
                      separators=(",", ":"), allow_nan=False).encode("ascii")


def _check_request(req):
    _require(type(req) is dict and set(req) == REQUEST_KEYS, "INVALID_REQUEST_SCHEMA")
    _require(req["protocol"] == SCHEMA, "INVALID_PROTOCOL")
    rid = req["request_id"]
    _require(type(rid) is str and len(rid) == 32 and
             all(x in "0123456789abcdef" for x in rid), "INVALID_REQUEST_ID")
    _require(type(req["expires_at_unix"]) is int and
             req["expires_at_unix"] > 0, "INVALID_EXPIRY")
    _require(req["hypotheses"] == list(HYPOTHESES), "HYPOTHESIS_LIST_MISMATCH")
    matrix = req["matrix"]
    _require(type(matrix) is list and len(matrix) == 16 and
             all(type(row) is list and len(row) == 24 and
                 all(type(bit) is int and bit in (0, 1) for bit in row)
                 for row in matrix), "MATRIX_INVALID")
    _require(len({tuple(row) for row in matrix}) == 16, "DUPLICATE_HYPOTHESES")
    obs = req["observations"]
    _require(type(obs) is list and len(obs) <= 5, "OBSERVATIONS_INVALID")
    used = set()
    active = list(HYPOTHESES)
    for event in obs:
        _require(type(event) is dict and set(event) == {"probe", "outcome"},
                 "OBSERVATION_SCHEMA_INVALID")
        probe, result = event["probe"], event["outcome"]
        _require(type(probe) is int and probe in PROBES and probe not in used,
                 "OBSERVATION_PROBE_INVALID")
        _require(type(result) is int and result in (0, 1),
                 "OBSERVATION_OUTCOME_INVALID")
        active = [h for h in active if matrix[HYPOTHESES.index(h)][probe] == result]
        _require(active, "OBSERVATIONS_CONTRADICTORY")
        used.add(probe)
    _require(req["candidate_names"] == active, "CANDIDATE_STATE_MISMATCH")
    avail = [p for p in PROBES if p not in used]
    _require(req["available_probes"] == avail, "AVAILABLE_PROBES_MISMATCH")
    _require(type(req["remaining_budget"]) is int and
             req["remaining_budget"] == 5-len(obs) and
             0 < req["remaining_budget"] <= 5 and len(active) > 1,
             "BUDGET_OR_ALREADY_SOLVED")
    _require(len(canonical_bytes(req)) <= 16384, "REQUEST_TOO_LARGE")
    return req


def issue_request(task, previous_observations, expires_at_unix, *, request_id=None):
    """Produce ONLY public challenge fields; truth, seed and evaluator secret excluded.

    The evaluator controls task generation, the deadline and private secret.
    This builder accepts a full task for convenience; do not pass an untrusted
    object with malicious side effects or use it as a security boundary.
    """
    _require(type(task) is dict and
             type(task.get("matrix")) is list, "INVALID_TASK")
    _require(type(previous_observations) is list, "INVALID_OBSERVATIONS")
    request_id = secrets.token_hex(16) if request_id is None else request_id
    used = set()
    active = list(HYPOTHESES)
    for event in previous_observations:
        _require(type(event) is dict and set(event) == {"probe", "outcome"},
                 "OBSERVATION_SCHEMA_INVALID")
        p, o = event["probe"], event["outcome"]
        _require(type(p) is int and p in PROBES and p not in used,
                 "OBSERVATION_PROBE_INVALID")
        _require(type(o) is int and o in (0, 1), "OBSERVATION_OUTCOME_INVALID")
        _require(len(task["matrix"]) == 16, "MATRIX_INVALID")
        active = [h for h in active if task["matrix"][HYPOTHESES.index(h)][p] == o]
        used.add(p)
    public = {
        "protocol": SCHEMA,
        "request_id": request_id,
        "expires_at_unix": expires_at_unix,
        "hypotheses": list(HYPOTHESES),
        "candidate_names": active,
        "matrix": [list(row) for row in task["matrix"]],
        "available_probes": [p for p in PROBES if p not in used],
        "observations": [{"probe": r["probe"], "outcome": r["outcome"]}
                         for r in previous_observations],
        "remaining_budget": 5-len(previous_observations),
    }
    return _check_request(public)


def request_digest(public_request):
    _check_request(public_request)
    return hashlib.sha256(canonical_bytes(public_request)).hexdigest()


def parse_response(raw):
    _require(type(raw) is bytes and 0 < len(raw) <= 512, "RESPONSE_SIZE")
    try:
        parsed = json.loads(raw.decode("utf-8", errors="strict"),
                            object_pairs_hook=_strict_object,
                            parse_constant=_bad_constant)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ProposalRejected("RESPONSE_NOT_JSON") from exc
    _require(type(parsed) is dict and set(parsed) == RESPONSE_KEYS, "RESPONSE_SCHEMA")
    return parsed


def admit_proposal(public_request, response_bytes, now_unix, spent_request_ids):
    """Only checks admission; DOES NOT execute an experiment or reserve an id.

    Caller MUST separately enforce durable atomic one-shot reservation, authority
    and runtime/cost budgets. A caller-provided set cannot protect concurrent runs.
    """
    _check_request(public_request)
    _require(type(now_unix) is int and now_unix >= 0, "INVALID_CLOCK")
    _require(now_unix < public_request["expires_at_unix"], "EXPIRED_REQUEST")
    _require(type(spent_request_ids) is set and
             all(type(x) is str for x in spent_request_ids), "SPENT_STATE_MISSING")
    rid = public_request["request_id"]
    _require(rid not in spent_request_ids, "REQUEST_ALREADY_SPENT")
    response = parse_response(response_bytes)
    _require(type(response["request_id"]) is str and
             response["request_id"] == rid, "CROSS_REQUEST_RESPONSE")
    dg = request_digest(public_request)
    _require(type(response["request_sha256"]) is str and
             response["request_sha256"] == dg, "REQUEST_DIGEST_MISMATCH")
    proposal = response["probe"]
    _require(type(proposal) is int and
             proposal in public_request["available_probes"], "INVALID_PROBE")
    return {"verdict": "ADMISSIBLE_PROPOSAL_ONLY",
            "request_id": rid, "probe": proposal,
            "request_sha256": dg}
